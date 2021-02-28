# -*- coding: utf-8 -*-
import json
import os
import re
import pymysql
from pymysql.cursors import DictCursor

SPACE = ' '
# LOCAL_GIT_PATH_ECE = r'C:\comWork\robotws5g\testsuite\RRM\ECE'
LOCAL_GIT_PATH_ECE = r'C:\comWork\Tools\ECE'

FILTERS = [
    "m_path like '%%Trunk%%'",
    "det_auto_lvl LIKE '%%22%%'",
    "test_entity in ('CIT', 'CRT')"
]
QUERY_CMD = "SELECT * FROM cn1_all_qc_instances WHERE " + " AND ".join(FILTERS)

DB_ARGUMENTS = {
    'host': 'xxx.xxx.xxx.xxx',
    'username': 'root',
    'password': 'uteadmin',
    'database': 'oep_db',
    'port': 3306
}


class DBConnection(object):
    def __init__(self, host, username, password, database, port):
        self.host = host
        self.username = username
        self.password = password
        self.database = database
        self.port = port

    def __enter__(self):
        self.conn = pymysql.connect(self.host, self.username, self.password, self.database, self.port)
        self.cur = self.conn.cursor(DictCursor)
        return self.cur

    def __exit__(self, *exc_info):
        self.cur.close()
        self.conn.close()


class AddNewTagsOrBranch(object):
    def __init__(self, command, tags=None, new_branch=None):
        self.command = command
        self.new_tags = tags
        self.new_branch = new_branch

    def run(self):
        names = self._get_all_cn1_test_cases_from_QC()
        print('Found QC total cases number: %s' % len(names))

        feature_names = self._get_feature_names_from_QC(names)
        print('Found related features number: %s' % len(feature_names))
        print(sorted(feature_names))

        robot_dict = self._get_robot_path_with_cases_from_GIT()
        print('Found local .robot files number: %s' % len(robot_dict.keys()))

        robot_paths = self._get_robot_path_matched_with_QC(names, robot_dict)
        print('Found .robot files matched with QC cases number: %s' % len(robot_paths))

        qc_paths = self._get_QC_file_paths_matched_with_robot(robot_paths)
        print('Found .qc files number: %s' % len(qc_paths))

        if self.command == 'add_tags':
            print('Add New Tags: %s' % self.new_tags)
            status = self._add_new_force_tags_for_robot_files(robot_paths)
        else:
            print('Add New Branch: %s' % self.new_branch)
            status = self._add_new_branch_to_qc_file(qc_paths, self.new_branch)
        if status:
            print('======================= Done. =======================')
        else:
            print('======================= Error Eccurred. Please Check. =======================')

    def _get_all_cn1_test_cases_from_QC(self):
        with DBConnection(**DB_ARGUMENTS) as cursor:
            cursor.execute(QUERY_CMD)
            cases = cursor.fetchall()
        names = [case['name'].strip() for case in cases]
        return names

    def _get_robot_path_with_cases_from_GIT(self):
        robot_dict = dict()
        for root, dirs, files in os.walk(LOCAL_GIT_PATH_ECE):
            for file in files:
                if file.endswith('.robot'):
                    file_path = os.path.join(root, file)
                    try:
                        case_names = self._get_case_names_from_robot_file(file_path)
                        if case_names:
                            robot_dict[file_path] = case_names.values()
                    except Exception:
                        print('[Warning] Errors occurred when get cases from %s.' % file_path)
        return robot_dict

    def _get_robot_path_matched_with_QC(self, qc_case_names, git_robot_dict):
        robot_paths = list()
        for name in qc_case_names:
            for key, val in git_robot_dict.items():
                if name in val and key not in robot_paths and self._is_feature_path(key):
                    robot_paths.append(key)
        return robot_paths

    def _is_feature_path(self, path):
        dir_name = os.path.dirname(path).split('\\')[-1]
        if dir_name.startswith(tuple(['5GC', 'FGCR', 'CNI', 'CB'])):
            return True
        return False

    def _get_feature_names_from_QC(self, case_names):
        feature_names = set()
        for name in case_names:
            feature = re.search(r'^[a-zA-Z0-9]+', name)
            if feature:
                feature_names.add(feature.group())
            else:
                feature = re.search(r'(?<=\])[a-zA-Z0-9]+', name)
                if feature:
                    feature_names.add(feature.group())
        return feature_names

    def _get_case_names_from_robot_file(self, file_name):
        case_names = dict()
        case_start = False
        content = self._get_file_content(file_name)
        if not re.search(r'(?i)\*{3}\s*test cases?\s*\*{3}', content):
            return case_names
        lines = self._get_file_content(file_name, lines=True)
        for index, line in enumerate(lines):
            if re.search(r'(?i)\*{3}\s*test cases?\s*\*{3}', line):
                case_start = True
                continue
            if re.search(r'(?i)\*{3}\s*(settings?|variables?|keywords?)\s*\*{3}', line):
                case_start = False
                continue
            if case_start and len(line.strip()) > 0 and not line.startswith(SPACE) and not line.startswith('#'):
                case_names[index + 1] = line.strip()
        return case_names

    def _get_QC_file_paths_matched_with_robot(self, robot_paths):
        ans = set()
        for path in robot_paths:
            dir_name = os.path.dirname(path)
            flag = False
            for name in os.listdir(dir_name):
                if name.endswith('.qc'):
                    ans.add(os.path.join(dir_name, name))
                    flag = True
            if not flag:
                print('[Warning] No .qc file found in %s' % dir_name)
        return ans

    def _add_new_force_tags_for_robot_files(self, robot_paths):
        """
        先判断是否有Settings，然后判断是否有Force Tags
        """
        for robot in robot_paths:
            try:
                content = self._get_file_content(robot)
                if not re.search(r'(?i)\*{3}\s*settings?\s*\*{3}', content):
                    self._add_settings_and_force_tags(robot)
                else:
                    match = re.search(r'(?mi)^Force Tags[ \w-]+(?:\n\.{3}[ \w-]+)*', content)
                    if not match:
                        self._add_force_tags(robot)
                    else:
                        self._update_force_tags(robot)
            except Exception:
                print('[Warning] Got errors when add tags in file %s' % robot)
                return False
        return True

    def _add_settings_and_force_tags(self, robot):
        content = self._get_file_content(robot)
        force_tags = self._get_force_tags(14, self.new_tags)
        new_content = "*** Settings ***\n" + force_tags + '\n\n' + content
        self._set_file_content(robot, new_content)

    def _add_force_tags(self, robot):
        content = self._get_file_content(robot)
        line = re.search(r'(?im)^.+(?=\n+\*{3}\s*(?:variables?|test cases?|keywords?))', content).group()
        s = re.search(r'^[\w#\.]+(?: ?\w+)*\s{2,}', line).group()
        length = len(s) if len(s) > 14 else 14
        force_tags = self._get_force_tags(length, self.new_tags)
        new_line = line + '\n' + force_tags
        new_content = content.replace(line, new_line)
        self._set_file_content(robot, new_content)

    def _update_force_tags(self, robot):
        content = self._get_file_content(robot)
        tags_content = re.search(r'(?mi)^Force Tags[ \w-]+(?:\n\.{3}[ \w-]+)*', content).group()
        current_tags = tags_content.replace('...', SPACE).split()[2:]
        tmp = list()
        for tag in current_tags + self.new_tags:
            if tag not in tmp:
                tmp.append(tag)
        length = len(re.search(r'(?mi)^Force Tags\s+', content).group())
        force_tags = self._get_force_tags(length, tmp)
        new_content = content.replace(tags_content, force_tags)
        self._set_file_content(robot, new_content)

    def _get_force_tags(self, pre_length, tags):
        force_tags = ''
        tmp = "Force Tags" + SPACE * (pre_length - 14)
        for tag in tags:
            if len(tmp + SPACE * 4 + tag) <= 120:  # make sure robot line not longer than 120
                tmp += SPACE * 4 + tag
            else:
                force_tags += tmp
                tmp = '\n...' + SPACE * (pre_length - 3) + tag
        force_tags += tmp
        return force_tags

    def _add_new_branch_to_qc_file(self, qc_paths=None, new_branch=None):
        new_branch = new_branch + '.*'
        for path in qc_paths:
            try:
                content = self._get_file_content(path)
                qc_dict = json.loads(content)
                if new_branch in qc_dict.keys():
                    print('[Warning] Branch already exists in %s' % path)
                    continue
                test_sets, root_path = self._get_target_test_sets_and_root_path(qc_dict, new_branch)
                if test_sets is None:
                    print('[Warning] Could not found trunk branch in %s' % path)
                    continue
                branch_dict = dict()
                branch_dict['label'] = '.*'
                branch_dict[root_path] = test_sets
                qc_dict[new_branch] = branch_dict
                qc_json = json.dumps(qc_dict, sort_keys=True, indent=4, separators=(',', ': '))
                self._set_file_content(path, qc_json)
            except Exception:
                print('[Warning] Got errors when add new branch in file %s' % path)
                return False
        return True

    def _get_target_test_sets_and_root_path(self, qc_dict, new_branch):
        new_branch_pre = new_branch.split('_')[0]
        branch_name = ''
        flag = False
        for key in qc_dict.keys():
            if key.startswith('5G_0.800'):
                branch_name = key
                flag = True
                break
        if not flag:
            return None, None
        for key, val in qc_dict.get(branch_name).items():
            if key.startswith('Root'):
                test_sets = val
                root_path = key.replace('Trunk', new_branch_pre + '\\Regression')
                break
        return test_sets, root_path

    def _get_file_content(self, path, lines=False):
        with open(path, 'r', encoding='utf-8') as f:
            if lines:
                content = f.readlines()
            else:
                content = f.read()
        return content

    def _set_file_content(self, path, content):
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)


if __name__ == '__main__':
    import sys
    if sys.version_info < (3, 0):
        print('Current script only support Python3.')
    else:
        argv = sys.argv
        if len(argv) < 2:
            print("Please at least input one command. Input 'python add_tags_or_branch.py --help' for more infos.")
        elif argv[1] == '--help':
            help_infos = """You have two options:
            1. Add new tags, example:      python add_tags_or_branch.py add_tags 5G00 CRT master_classicalbts_all
            2. Create new branch, example: python add_tags_or_branch.py new_branch 5G21A_10.1800
            """
            print(help_infos)
        elif argv[1] == 'add_tags':
            if len(argv) < 3:
                print('Please give at least one new tags...')
            else:
                obj = AddNewTagsOrBranch(command=argv[1], tags=argv[2:])
                obj.run()
        elif argv[1] == 'new_branch':
            if len(argv) < 3:
                print('Please give your new branch name...')
            else:
                obj = AddNewTagsOrBranch(command=argv[1], new_branch=argv[2])
                obj.run()
        else:
            print('Given command "%s" is not supported, please input --help for more infos.' % argv[1])
