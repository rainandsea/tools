# -*- coding: utf-8 -*-
"""
:created on: 2020-07-29
:author: Huaiyuan Liu
"""
from sqlalchemy import create_engine
from ute_cloud_manager_api.api import CloudManagerApi
import pandas as pd
import time
import re
import os
import requests

BASE_DIRECTORY = os.path.abspath(os.path.join(os.path.dirname("__file__"), os.path.pardir))
LOG_DIRECTORY = os.path.join(BASE_DIRECTORY, 'logs/')

TOKENS = {
    'xxx1': 'b6fd0901665802f9ea6350e50ebd12e2f4a43a71',
    'xxx2': '517b633f8adbce12af28195e7ec5caaa3468cf28',
    'xxx3': '8a14d5cd2000fd1e576662a1a21fe3a19f9de880',
    'xxx4': '1ac26e26d6eae12283efbd59acf837d243bf9a00',
    'xxx5': '3a5879340dcd3fa060c4c2000cbadd1dac302788'
}


class GitParser(object):
    def __init__(self):
        self.sign_in_url = 'https://xxx.com/users/sign_in'
        self.login_url = 'https://xxx.com/users/auth/ldapmain/callback'
        self.case_url = 'https://xxx.com/5G/robotws5g/blob/master/'
        self.tags_scope = ['A', 'B', 'C', 'D', 'E', 'F']
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36',
            'referer': 'https://xxx.com/users/sign_in'
        }
        self.session = requests.Session()

    def run_and_get_tags(self, path):
        self._login()
        content = self._get_robot_content(path)
        return self._get_tags(content)

    def _login(self):
        response = self.session.get(self.sign_in_url)
        assert response.status_code == 200
        form_data = {
            'utf8': '✓',
            'authenticity_token': self._get_csrf_token(response.text),
            'username': 'admin',
            'password': 'admin'
        }

        res = self.session.post(self.login_url, data=form_data, headers=self.headers)
        assert res.status_code == 200

    def _get_robot_content(self, path):
        response = self.session.get(
            self.case_url + path + '?format=json&viewer=simple')
        assert response.status_code == 200
        return response.text

    def _get_csrf_token(self, text):
        token = re.findall(r'<meta name="csrf-token" content="(.*)" />', text)
        return token[0] if token else None

    def _get_tags(self, text):
        tags = set(re.findall(r'5G_[A-Z_]+', text))
        return [tag for tag in tags if tag in self.tags_scope] if tags else None


class CreateSingleRuns(object):
    def __init__(self):
        self.db_url = "mysql+pymysql://root:uteadmin@xxx.xxx.xxx.xxx:3306/oep_db"
        self.engine = create_engine(self.db_url)
        self.api = CloudManagerApi(api_token='1eb5f850408fbe9e34f584174465017d90247921')
        self.parser = GitParser()

        self.tags_scope = ['A', 'B', 'C', 'D', 'E', 'F']
        self.branchs_scope = ['branch_a', 'branch_b']  # for now, only trunk supported
        self.result_scope = ['not analyzed', 'environment issue']

        self.qc_cases = []
        self.single_run_candidates = []

        self.base_case_infos = {
            'test_path': None,                      # Mandatory
            'testline_type': None,                  # Mandatory
            'enb_build': self._get_latest_build(),  # Mandatory
            'ute_build': None,
            'sysimage_build': None,
            'test_repository_revision': None,
            'skiprun': None,
            'testline_type_tag': None,
            'enb_build_tag': None,
            'state': None,                          # default configured
            'tags': None,                           # Mandatory, ['5G_RAN_TDD']
            'include_tags': None,
            'additional_options': None,
            'tester': None                          # remove it when create single run
        }

    def run(self):
        self._get_single_run_candidates()
        print(self.single_run_candidates)
        print(len(self.single_run_candidates))
        for candidate in self.single_run_candidates:
            try:
                api = CloudManagerApi(api_token=TOKENS.get(candidate.pop('tester'), TOKENS.get('huailiu')))
                execution_id = api.create_single_run(**candidate)
                self._log('success', candidate, execution_id)
            except Exception as e:
                self._log('failed', candidate)

    def _get_single_run_candidates(self):
        sql_1 = "SELECT * FROM oep_table_qc WHERE last_exec_cloud='1' AND det_auto_lvl='22 - Test execution is fully automated, Analysis is fully automated'"
        sql_2 = "SELECT * FROM oep_table_test_runs"
        sql_3 = "DESC oep_table_test_runs"

        cases_in_qc = self.engine.execute(sql_1).fetchall()
        self.qc_cases = [case['name'] for case in cases_in_qc]

        test_runs = self.engine.execute(sql_2).fetchall()
        test_runs_columns = [column[0] for column in self.engine.execute(sql_3).fetchall()]
        test_runs_df = pd.DataFrame(test_runs, columns=test_runs_columns)

        for case in self.qc_cases:
            filter_res = test_runs_df[test_runs_df['name'] == case].sort_values(
                by='benchmark_date', axis=0, ascending=False)
            if filter_res.shape[0] != 0 and filter_res.iloc[0]['summed_result'] in self.result_scope:
                paths_exist = [case['test_path'] for case in self.single_run_candidates]
                if filter_res.iloc[0]['test_suite'] not in paths_exist:
                    infos = self.base_case_infos.copy()
                    infos['test_path'] = filter_res.iloc[0]['test_suite']
                    infos['testline_type'] = filter_res.iloc[0]['testline_type']
                    # infos['enb_build'] = self._get_latest_build()
                    infos['tags'] = self._get_case_tags(filter_res.iloc[0]['test_suite'])
                    infos['tester'] = self._get_tester_name(filter_res.iloc[0]['res_tester'])
                    self.single_run_candidates.append(infos)

    def _get_latest_build(self):
        builds = self.api.list_enb_builds(branch=self.branchs_scope[0], limit=1)
        return builds[0]['name']

    def _get_case_tags(self, path):
        try:
            tags = self.parser.run_and_get_tags(path)
            return tags if tags else None
        except Exception as e:
            self._log('Get tags from git failed for case: ' + path)

    def _get_tester_name(self, tester):
        return tester[tester.index('(') + 1: tester.index(')')]

    def _log(self, result, candidate, execution_id=None):
        with open(LOG_DIRECTORY + 'auto_re_run.log', 'a+') as f:
            f.writelines('[%s]create single run %s: %s, execution id: %s\n' % (
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                result,
                candidate['test_path'],
                execution_id))


if __name__ == '__main__':
    obj = CreateSingleRuns()
    obj.run()
