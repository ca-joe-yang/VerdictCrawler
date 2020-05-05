import json
from datetime import datetime
from urllib.parse import urlencode

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import requests
import re

SUNNY_JUDGE_API = 'https://api.jrf.org.tw'
SUNNY_JUDGE_COURT = SUNNY_JUDGE_API + '/courts'
SUNNY_JUDGE_SEARCH_API = SUNNY_JUDGE_API + '/search/stories?'

def gen_search_query(**kwargs):

	query = {
		'page': '',
		'q[adjudged_on_gteq]': '',
		'q[adjudged_on_lteq]': '',
		'q[judges_names_cont]': '',
		'q[lawyer_names_cont]': '',
		'q[number]': '',
		'q[story_type]': '',
		'q[word]': '',
		'q[year]': ''
	}

	for key, value in kwargs.items():

		if key == 'page':
			query[key] = value
		else:
			key = 'q[' + key + ']'
			query[key] = value

	return SUNNY_JUDGE_SEARCH_API + urlencode(query)

def gen_verdict_name(x):
	v_type = x['type']
	v_year = str(x['year'])
	v_word = x['word']
	v_number = str(x['number'])
	return '_'.join([v_type, v_year, v_word, v_number])

def time_format(t):
	return '-'.join([t[:4], t[4:6], t[6:]])

def handle_query(x):
	response = requests.get(x, verify=False)
	if response.status_code != 200:
		return None
	return json.loads(response.text)


start_time = '20170101'
end_time = '20170102'
story_type = '刑事'

start_time = time_format(start_time)
end_time = time_format(end_time)

next_query = gen_search_query(adjudged_on_gteq=start_time, adjudged_on_lteq=end_time, story_type=story_type)
verdict_count = 0
page_count = 0
while True:
	print('Searching verdicts of {}-type from {} to {}'.format(story_type, start_time, end_time))
	search_result = handle_query(next_query)

	if search_result is None:
		break

	n_verdict = search_result['pagination']['count']
	print('Search result: {} verdicts found'.format(n_verdict))
	for story in search_result['stories']:
		verdict_url = story['detail_url'] + '/verdict'
		verdict = handle_query(verdict_url)['verdict']
		verdict_name = gen_verdict_name(verdict['story']['identity'])
		verdict_count += 1
		print('Processing {} / {}: {}'.format(verdict_count, n_verdict, verdict_name))

		if verdict is None:
			continue

		verdict_content_url = verdict['body']['content_url']
		verdict_content = handle_query(verdict_content_url)

		if verdict_content is None:
			continue

		verdict_content = verdict_content['main_content'].replace('\r', '').replace('\n', '')
		verdict_content = re.sub(' +', ' ', verdict_content)
		verdict['content'] = verdict_content
		with open(verdict_name + '.json', 'w', encoding="utf-8") as f:
			json.dump(verdict, f, indent=4, ensure_ascii=False)

		index = verdict_content.find('判決如下')
		index = verdict_content.find('無罪', index + 100)
		if index != -1:
			print('無罪')
		index = verdict_content.find('有期', index + 100)
		if index != -1:
			print(verdict_content[index:index+10])


		#break
	next_query = search_result['pagination']['next_url']
	if next_query is None:
		break


