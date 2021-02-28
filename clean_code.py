# -*- coding: utf-8 -*-
"""
This tool is designed to check robot files
"""
import os
import re

MAX_KEYWORD_ARGUMENTS = 5
MAX_LINE_COLUMNS = 150
MAX_ROBOT_FILE_LINE_NUMS = 800
MAX_KEYWORD_STEPS = 20
MAX_CASE_STEPS = 15
MAX_FOR_LOOP_STEPS = 5
BOOLEAN_VALUES = ['true', '${true}', 'false', '${false}']
SPACE = ' '
LOG_NAME = 'clean_code.log'
SPECIAL_KEYWORDS = [
    'run keyword',
    'run keyword and continue on failure',
    'run keyword and expect error',
    'run keyword and ignore error',
    'run keyword and return'
    'run keyword and return if',
    'run keyword and return status',
    'run keyword if',
    'run keyword if all critical tests passed',
    'run keyword if all tests passed',
    'run keyword if any critical tests failed',
    'run keyword if any tests failed',
    'run keyword if test failed',
    'run keyword if test passed',
    'run keyword if timeout occurred',
    'run keyword unless',
    'run keywords',
    'wait until keyword succeeds',
    'repeat keyword',
    'else'
]
SPECIAL_OPTIONS = [
    '[Arguments]',
    '[Documentation]'
]

UP_AND_DOWNS = [
    'Suite Setup',
    'Suite Teardown',
    'Test Setup',
    'Test Teardown',
    '[Setup]',
    '[Teardown]'
]

TITLE_BEFORE = '\n' + '-' * 90 + '\n'
TITLE_AFTER = '\n' + '-' * 90 + '\n'


class CleanCode(object):
    def __init__(self, target_directory):
        self.target_directory = target_directory
        self.robot_files = self._get_all_robot_files()
        self.check_result = True

    def run(self):
        self.run_checks()
        self.run_format()

    def run_checks(self):
        if os.path.exists(LOG_NAME):
            os.remove(LOG_NAME)
        self.check_keyword_arguments_no_more_than_5()
        self.check_keyword_arguments_not_boolean()
        self.check_robot_line_shall_not_longer_than_150_columns()
        self.check_robot_file_counts_no_more_than_800()
        self.check_case_name_should_be_titled_with_underline()
        self.check_keyword_name_should_be_titled_with_space()
        self.check_global_suite_test_variables_should_be_uppercase_with_underline()
        # self.check_local_variables_should_be_lowercase_with_underline()
        self.check_keyword_steps_no_more_than_20()
        self.check_case_steps_no_more_than_15()
        self.check_for_loop_steps_no_more_than_5()
        self.check_if_sleep_is_allowed()
        # self.check_interval_should_be_4_spaces()
        self.check_if_robot_contains_tab()
        if self.check_result:
            self._show_log('\nCongratulations. All Check Points Passed...')
        else:
            self._show_log('\n!!!!!!!!!! You Got Check Points Failed, Please Check Carefully !!!!!!!!!!')
        print('Done. Please find clean_code.log here: %s' % os.getcwd())

    def run_format(self):
        self.format_replace_tabs_with_4_spaces()
        self.format_remove_useless_spaces_and_alignment()
        self.format_keywords()

    def check_keyword_arguments_no_more_than_5(self):
        self._show_log('check keyword arguments no more than 5', title=True)
        for file_name in self.robot_files:
            args_counter = self._get_keyword_arguments_more_than_5(file_name)
            self._show_all_candidates(file_name, args_counter, 'Arguments Count')
            if args_counter:
                self.check_result = False

    def check_keyword_arguments_not_boolean(self):
        self._show_log('check keyword arguments not boolean', title=True)
        for file_name in self.robot_files:
            args_boolean = self._get_keyword_arguments_is_boolean(file_name)
            self._show_all_candidates(file_name, args_boolean, 'Argument has boolean value')
            if args_boolean:
                self.check_result = False

    def check_robot_line_shall_not_longer_than_150_columns(self):
        self._show_log('check robot line shall not longer than 150 columns', title=True)
        for file_name in self.robot_files:
            long_lines = self._get_robot_line_longer_than_150_columns(file_name)
            self._show_all_candidates(file_name, long_lines, 'Line Length')
            if long_lines:
                self.check_result = False

    def check_robot_file_counts_no_more_than_800(self):
        self._show_log('check robot file counts no more than 800', title=True)
        for file_name in self.robot_files:
            if self._if_robot_file_line_more_than_800(file_name):
                self._show_log('File Name: %s, line counts more than 800' % file_name)
                self.check_result = False

    def check_case_name_should_be_titled_with_underline(self):
        self._show_log('check case name should be titled with underline and no special character', title=True)
        for file_name in self.robot_files:
            case_names = self._get_test_case_names_not_recommend(file_name)
            self._show_all_candidates(file_name, case_names, 'Case Name')
            if case_names:
                self.check_result = False

    def check_keyword_name_should_be_titled_with_space(self):
        self._show_log('check keyword name should be titled with space', title=True)
        for file_name in self.robot_files:
            all_keywords = self._get_keywords_not_recommend(file_name)
            self._show_all_candidates(file_name, all_keywords, 'Keyword')
            if all_keywords:
                self.check_result = False

    def check_global_suite_test_variables_should_be_uppercase_with_underline(self):
        """
        not sure how to get all candidate variables in other files
        """
        self._show_log('check global/suite/test variables should be uppercase with underline', title=True)
        for file_name in self.robot_files:
            all_variables = self._get_global_suite_test_variables_not_recommend(file_name)
            self._show_all_candidates(file_name, all_variables, 'Variable')
            if all_variables:
                self.check_result = False

    def check_local_variables_should_be_lowercase_with_underline(self):
        """
        not sure how to get all candidate variables in other files
        """
        self._show_log('check local variables should be lowercase with underline', title=True)
        for file_name in self.robot_files:
            # print(file_name)
            all_local_variables = self._get_local_variables_not_recommend(file_name)
            if all_local_variables:
                self.check_result = False

    def check_keyword_steps_no_more_than_20(self):
        self._show_log('check keyword steps no more than 20', title=True)
        for file_name in self.robot_files:
            keywords_steps = self._get_keywords_steps_more_than_20(file_name)
            self._show_all_candidates(file_name, keywords_steps, 'Step Number')

    def check_case_steps_no_more_than_15(self):
        self._show_log('check case steps no more than 15', title=True)
        for file_name in self.robot_files:
            case_steps = self._get_case_steps_more_than_15(file_name)
            self._show_all_candidates(file_name, case_steps, 'Step Number')
            if case_steps:
                self.check_result = False

    def check_for_loop_steps_no_more_than_5(self):
        self._show_log('check for loop steps no more than 5', title=True)
        for file_name in self.robot_files:
            for_loop_steps = self._get_for_loop_steps_more_than_5(file_name)
            self._show_all_candidates(file_name, for_loop_steps, 'For loop steps number')
            if for_loop_steps:
                self.check_result = False

    def check_if_sleep_is_allowed(self):
        self._show_log('check if sleep is allowed', title=True)
        for file_name in self.robot_files:
            not_allowed_sleeps = self._get_not_allowed_sleep(file_name)
            self._show_all_candidates(file_name, not_allowed_sleeps, 'Content')
            if not_allowed_sleeps:
                self.check_result = False

    def check_interval_should_be_4_spaces(self):
        self._show_log('check if interval is 4 spaces', title=True)

    def check_if_robot_contains_tab(self):
        self._show_log('check if robot contains tab', title=True)
        for file_name in self.robot_files:
            tabs = self._get_tabs(file_name)
            self._show_all_candidates(file_name, tabs, 'Content')
            if tabs:
                self.check_result = False

    def format_replace_tabs_with_4_spaces(self):
        for file_name in self.robot_files:
            tabs = self._get_tabs(file_name)
            if tabs:
                with open(file_name, 'r+') as f:
                    content = f.read()
                content = content.replace('\t', SPACE * 4)
                with open(file_name, 'w') as f:
                    f.write(content)

    def format_remove_useless_spaces_and_alignment(self):
        for file_name in self.robot_files:
            s_len = self._get_max_settings_or_variable_length(file_name, 'settings')
            v_len = self._get_max_settings_or_variable_length(file_name, 'variable')
            s_content = self._get_settings_format_content(file_name, s_len)
            v_content = self._get_variable_format_content(file_name, v_len)
            t_content = self._get_test_case_format_content(file_name)
            k_content = self._get_keywords_format_content(file_name)
            with open(file_name, 'w') as f:
                for index, line in enumerate(s_content + v_content + t_content + k_content):
                    if index == 0:
                        f.writelines(line.strip() + '\n')
                    else:
                        f.writelines(line + '\n')

    def format_keywords(self):
        for file_name in self.robot_files:
            all_keywords = self._get_keywords_not_recommend(file_name)
            # print(file_name, all_keywords)
            with open(file_name, 'r') as f:
                content = f.read()
                for keywords in all_keywords.values():
                    for keyword in keywords:
                        if '.' in keyword:
                            keyword = keyword.split('.')[-1]
                        words = keyword.replace('_', ' ').replace('-', ' ').split()
                        new_keyword = ' '.join([w[0].upper() + w[1:] for w in words])
                        content = content.replace(keyword, new_keyword)
            with open(file_name, 'w') as f:
                f.write(content)

    def _get_settings_format_content(self, file_name, s_len):
        content = list()
        mark_start = False
        with open(file_name, 'r') as f:
            for line in f.readlines():
                if re.search(r'(?i)\*{3}\s*settings?\s*\*{3}', line):
                    mark_start = True
                    content.append('*** Settings ***')
                elif re.search(r'(?i)\*{3}\s*(variables?|test cases?|keywords?)\s*\*{3}', line):
                    return content
                else:
                    if mark_start and line.strip():
                        line_values = [val.strip() for val in line.split(SPACE * 2) if val]
                        option = line_values[0]
                        others = line_values[1:]
                        line_format = option + (s_len - len(option) + 4) * SPACE + '    '.join(others)
                        content.append(line_format)
        return content

    def _get_variable_format_content(self, file_name, v_len):
        content = list()
        mark_start = False
        with open(file_name, 'r') as f:
            for line in f.readlines():
                if re.search(r'(?i)\*{3}\s*variables?\s*\*{3}', line):
                    mark_start = True
                    content.append('\n*** Variables ***')
                elif re.search(r'(?i)\*{3}\s*(test cases?|keywords?)\s*\*{3}', line):
                    return content
                else:
                    if mark_start and line.strip():
                        line_values = [val.strip() for val in line.split(SPACE * 2) if val]
                        var_name = line_values[0]
                        var_vals = line_values[1:]
                        line_format = var_name + (v_len - len(var_name) + 4) * SPACE + '    '.join(var_vals)
                        content.append(line_format)
        return content

    def _get_test_case_format_content(self, file_name):
        content = list()
        mark_start = False
        first_case_found = False
        with open(file_name, 'r') as f:
            for line in f.readlines():
                if re.search(r'(?i)\*{3}\s*test cases?\s*\*{3}', line):
                    mark_start = True
                    content.append('\n*** Test Cases ***')
                elif re.search(r'(?i)\*{3}\s*keywords?\s*\*{3}', line):
                    return content
                else:
                    if mark_start and line.strip():
                        if not line.startswith(tuple([SPACE, '#'])):
                            case_name = line.strip()
                            if first_case_found:
                                content.append('\n' + case_name)
                            else:
                                content.append(case_name)
                                first_case_found = True
                        else:
                            line_values = [val.strip() for val in line.split(SPACE * 2) if val]
                            line_format = SPACE * 4 + '    '.join(line_values)
                            content.append(line_format)
        return content

    def _get_keywords_format_content(self, file_name):
        content = list()
        mark_start = False
        first_keyword_found = False
        with open(file_name, 'r') as f:
            for line in f.readlines():
                if re.search(r'(?i)\*{3}\s*keywords?\s*\*{3}', line):
                    mark_start = True
                    content.append('\n*** Keywords ***')
                else:
                    if mark_start and line.strip():
                        if not line.startswith(tuple([SPACE, '#'])):
                            case_name = line.strip()
                            if first_keyword_found:
                                content.append('\n' + case_name)
                            else:
                                content.append(case_name)
                                first_keyword_found = True
                        else:
                            line_values = [val.strip() for val in line.split(SPACE * 2) if val]
                            line_format = SPACE * 4 + '    '.join(line_values)
                            content.append(line_format)
        return content

    def _get_all_robot_files(self):
        robot_files = list()
        for root, dirs, files in os.walk(self.target_directory):
            for file in files:
                if self._get_file_type(file) == 'robot':
                    robot_files.append('\\'.join([root, file]))
        return robot_files

    def _get_global_suite_test_variables_not_recommend(self, file_name):
        variables = dict()
        with open(file_name, 'r') as f:
            for index, line in enumerate(f.readlines()):
                if line.startswith(tuple('$@&%')):
                    variable = line.split()[0]
                    if not self._is_variable_recommend(variable):
                        variables[index + 1] = variable
                        continue
                matches = re.findall(r"(?i)set[\s_](?:suite|global|test)[\s_]variable\s+(?P<var>[$@&%]\{.*?\})", line)
                if matches and not self._is_variable_recommend(matches[0]):
                    variables[index + 1] = matches[0]
        return variables

    def _get_local_variables_not_recommend(self, file_name):
        none_local_variables = self._get_global_suite_test_variables_not_recommend(file_name)
        local_variables = dict()
        with open(file_name, 'r') as f:
            for index, line in enumerate(f.readlines()):
                matches = re.findall(r"[$@&%]\{.*?\}", line)
                for match in matches:
                    if match not in none_local_variables.values():
                        local_variables[index + 1] = local_variables.get(index + 1, list()) + [match]
        return local_variables

    def _get_test_case_names_not_recommend(self, file_name):
        case_names = dict()
        case_start = False

        with open(file_name, 'r') as f:
            if not re.search(r'(?i)\*{3}\s*test cases?\s*\*{3}', f.read()):
                return case_names

        with open(file_name, 'r') as f:
            for index, line in enumerate(f.readlines()):
                if re.search(r'(?i)\*{3}\s*test cases?\s*\*{3}', line):
                    case_start = True
                    continue
                if re.search(r'(?i)\*{3}\s*(settings?|variables?|keywords?)\s*\*{3}', line):
                    case_start = False
                    continue
                if case_start and len(line.strip()) > 0 and not line.startswith(SPACE) and not line.startswith('#'):
                    if not self._is_case_name_recommend(line.strip()):
                        case_names[index + 1] = line.strip()

        return case_names

    def _get_case_steps_more_than_15(self, file_name):
        case_start = False
        step_start = False
        steps = 0
        row_index = 0
        case_name = ''
        case_steps = dict()
        with open(file_name, 'r') as f:
            for index, line in enumerate(f.readlines()):
                if re.search(r'(?i)\*{3}\s*(settings?|variables?|keywords?)\s*\*{3}', line):
                    case_start = False
                    continue
                if re.search(r'(?i)\*{3}\s*test cases?\s*\*{3}', line):
                    case_start = True
                    continue
                if case_start and not line.startswith(tuple('# ')):
                    if case_name and steps > MAX_CASE_STEPS:
                        case_steps[str(row_index) + ', ' + case_name] = steps
                    case_name = line.strip()
                    row_index = index + 1
                    step_start = False
                    steps = 0
                    continue
                if case_start and not line.strip().startswith(tuple(['[', '...', '#'])):
                    step_start = True
                    steps += 1
                    continue
                if step_start and line.strip() and not line.strip().startswith('['):
                    steps += 1
        if case_name and steps > MAX_CASE_STEPS:
            case_steps[str(row_index) + ', ' + case_name] = steps
        return case_steps

    def _get_keywords_not_recommend(self, file_name):
        current_index = 0
        all_keywords = dict()
        with open(file_name, 'r') as f:
            for index, line in enumerate(f.readlines()):
                if not line.strip():
                    continue
                if line.strip().startswith('#'):
                    continue
                if re.search(r'(?i)\*{3}\s*settings?\s*\*{3}', line):
                    current_index = 1
                    continue
                if re.search(r'(?i)\*{3}\s*test cases?\s*\*{3}', line):
                    current_index = 3
                    continue
                if re.search(r'(?i)\*{3}\s*keywords?\s*\*{3}', line):
                    current_index = 4
                    continue
                if current_index == 3 and not line.startswith(SPACE * 2):
                    continue
                text_list = self._get_text_list(line.strip('\n'))
                if text_list:
                    if current_index == 1 and text_list[0].title() in UP_AND_DOWNS:
                        line_keywords = self._find_all_keywords_in_line(text_list[1:])
                        if line_keywords:
                            all_keywords[index + 1] = line_keywords
                    if current_index == 3 or current_index == 4:
                        if text_list[0].title() in UP_AND_DOWNS or text_list[0][0] not in '[.':
                            line_keywords = self._find_all_keywords_in_line(text_list)
                            if line_keywords:
                                all_keywords[index + 1] = line_keywords
        return all_keywords

    def _get_keywords_steps_more_than_20(self, file_name):
        keyword_start = False
        step_start = False
        steps = 0
        row_index = 0
        keyword = ''
        keywords_steps = dict()
        with open(file_name, 'r') as f:
            for index, line in enumerate(f.readlines()):
                if re.search(r'(?i)\*{3}\s*(settings?|variables?|test cases?)\s*\*{3}', line):
                    keyword_start = False
                    continue
                if re.search(r'(?i)\*{3}\s*keywords?\s*\*{3}', line):
                    keyword_start = True
                    continue
                if keyword_start and not line.startswith(tuple('# ')):
                    if keyword and steps > MAX_KEYWORD_STEPS:
                        keywords_steps[str(row_index) + ', ' + keyword] = steps
                    keyword = line.strip()
                    row_index = index + 1
                    step_start = False
                    steps = 0
                    continue
                if keyword_start and not line.strip().startswith(tuple(['[', '...', '#'])):
                    step_start = True
                    steps += 1
                    continue
                if step_start and line.strip() and not line.strip().startswith('['):
                    steps += 1
        if keyword and steps > MAX_KEYWORD_STEPS:
            keywords_steps[str(row_index) + ', ' + keyword] = steps
        return keywords_steps

    def _get_file_type(self, file_name):
        vals = file_name.split('.')
        return vals[-1] if vals[-1] in ['py', 'robot'] else None

    def _get_keyword_arguments_more_than_5(self, file_name):
        """
        return: a dict contains row number and args values count
        """
        args_counter = dict()
        with open(file_name, 'r') as f:
            for index, line in enumerate(f.readlines()):
                if line.strip().startswith('[Arguments]') and len(line.split()) - 1 > MAX_KEYWORD_ARGUMENTS:
                    args_counter[index + 1] = len(line.split()) - 1
        return args_counter

    def _get_keyword_arguments_is_boolean(self, file_name):
        args_boolean = dict()
        with open(file_name, 'r') as f:
            for index, line in enumerate(f.readlines()):
                if line.strip().startswith('[Arguments]'):
                    for argument in line.split()[1:]:
                        if argument.split('=')[-1].lower() in BOOLEAN_VALUES:
                            args_boolean[index + 1] = argument.split('=')[0]
        return args_boolean

    def _get_robot_line_longer_than_150_columns(self, file_name):
        long_lines = dict()
        with open(file_name, 'r') as f:
            for index, line in enumerate(f.readlines()):
                if len(line) >= MAX_LINE_COLUMNS:
                    long_lines[index + 1] = len(line)
        return long_lines

    def _if_robot_file_line_more_than_800(self, file_name):
        with open(file_name, 'r') as f:
            if len(f.readlines()) > MAX_ROBOT_FILE_LINE_NUMS:
                return True
        return False

    def _is_case_name_recommend(self, name):
        if SPACE in name or '-' in name:
            return False
        if sum([True for c in '~!@#$%^&*(){}:"<>?|`[];,./+=' if c in name]) > 0:
            return False
        for word in name.split('_'):
            if word[0].islower():
                return False
        return True

    def _get_text_list(self, line_content):
        text_list = line_content.split(SPACE * 2)
        text_list = self._remove_blank_spaces(text_list)
        return text_list

    def _remove_blank_spaces(self, text_list):
        new_text_list = []
        for text in text_list:
            if text:
                new_text_list.append(text.strip())
        return new_text_list if new_text_list else None

    def _find_all_keywords_in_line(self, text_list):
        keywords = list()
        if text_list[0] in SPECIAL_OPTIONS:
            return keywords
        for text in text_list:
            if self._is_keyword(text):
                if not self._is_keyword_recommend(text):
                    keywords.append(text)
                if not text.replace('_', ' ').replace('-', ' ').lower() in SPECIAL_KEYWORDS:
                    break  # only one keyword in this line
        return keywords

    def _is_keyword(self, item):
        if item[0].isdigit():
            return False
        if item in ['_', ';', '.', '\\', '\n', '...']:
            return False
        for char in ['=', '$', '@', '&', ':', '[', ']', '\\', '|', '/', '%', '*', '^']:
            if char in item:
                return False
        return True

    def _is_keyword_recommend(self, keyword):
        if '.' in keyword:
            keyword = keyword.split('.')[-1]
        if '_' in keyword:
            return False
        if '-' in keyword:
            return False
        for word in keyword.split():
            if word[0].islower():
                return False
        return True

    def _is_variable_recommend(self, var):
        if '-' in var:
            return False
        if ' ' in var:
            return False
        if not var.isupper():
            return False
        return True

    def _get_for_loop_steps_more_than_5(self, file_name):
        for_start = False
        row_index = 0
        steps = 0
        for_loop_steps = dict()
        with open(file_name, 'r') as f:
            for index, line in enumerate(f.readlines()):
                if line.strip().startswith(':FOR'):
                    for_start = True
                    row_index = index + 1
                    continue
                if for_start:
                    if line.strip().startswith('\\'):
                        steps += 1
                    else:
                        if steps > MAX_FOR_LOOP_STEPS:
                            for_loop_steps[row_index] = steps
                        for_start = False
                        steps = 0
        if for_start and steps > MAX_FOR_LOOP_STEPS:
            for_loop_steps[row_index] = steps
        return for_loop_steps

    def _get_not_allowed_sleep(self, file_name):
        pre = ''
        not_allowed_sleeps = dict()
        with open(file_name, 'r') as f:
            for index, line in enumerate(f.readlines()):
                if line.strip().startswith('#'):
                    continue
                if re.search(r'(?i)sleep\s{2,}', line) and not re.search(r'(?i)(log|traffic|trf_data_start)', pre):
                    not_allowed_sleeps[index + 1] = line.strip()
                pre = line
        return not_allowed_sleeps

    def _get_tabs(self, file_name):
        tabs = dict()
        with open(file_name, 'r') as f:
            for index, line in enumerate(f.readlines()):
                if re.search(r'\t', line):
                    tabs[index + 1] = line.strip('\n')
        return tabs

    def _show_all_candidates(self, file_name, candidates, label):
        """
        candidates: a dict with line index as keys
        """
        mark = True
        for line_index in sorted(candidates.keys()):
            if mark:
                self._show_log('\nFile Name: ' + file_name)
                mark = False
            self._show_log('Line Index: %s, %s: %s' % (line_index, label, candidates.get(line_index)))

    def _get_max_settings_or_variable_length(self, file_name, option):
        if option == 'settings':
            pattern1 = r'(?i)\*{3}\s*settings?\s*\*{3}'
            pattern2 = r'(?i)\*{3}\s*(variables?|test cases?|keywords?)\s*\*{3}'
        else:
            pattern1 = r'(?i)\*{3}\s*variables?\s*\*{3}'
            pattern2 = r'(?i)\*{3}\s*(settings?|test cases?|keywords?)\s*\*{3}'
        ans = 0
        with open(file_name, 'r') as f:
            content = f.read()
            if not re.search(pattern1, content):
                return ans
        mark = False
        with open(file_name, 'r') as f:
            for line in f.readlines():
                if re.search(pattern1, line):
                    mark = True
                    continue
                if re.search(pattern2, line):
                    mark = False
                    continue
                if mark and line.strip() and not line.strip().startswith(tuple(['#', '...', '\n'])):
                    ans = max(ans, len(line.strip().split(SPACE * 2)[0]))
        return ans

    def _show_log(self, content, title=False):
        with open(LOG_NAME, 'a+') as f:
            if title:
                line = '*' * 8 + SPACE + content + SPACE + '*' * 8
                f.writelines(TITLE_BEFORE + line + TITLE_AFTER)
            else:
                f.writelines(content + '\n')


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print('Please give your robot files directory...')
    elif not os.path.isdir(sys.argv[1]):
        print('Given path is not a directory or directory not exists: %s' % sys.argv[1])
    else:
        obj = CleanCode(sys.argv[1])
        obj.run()
