#!/usr/bin/env python
# coding: utf-8
'''
vote4haruppi.py: the voting script for Haruka Kodama.
'''
__author__ = 'meroppi'

import os
import traceback
import urllib
import urllib.request
import urllib.parse
import http
import http.cookiejar
from html.parser import HTMLParser

print('''
============================
AKB48 41st シングル選抜総選挙
兒玉遥投票スクリプト
============================
''')

# はるっぴの投票番号
candidate_code = "40109"

# 投票コードファイル名
vote_file_name = 'votecode.txt'

# 投票結果の保存先ディレクトリ
destdir = 'results'

# 投票先のURL等
base_url = 'http://akb48-sousenkyo.jp/web/akb2015/vote'
vote_url = base_url + '/thanks'
xsrf_param_name = 'vote_form_sys.xsrf'

class Voter:
	def __init__(self, candidate_code, serial1, serial2):
		self.candidate_code = candidate_code
		self.serial_number = serial1 + ' ' + serial2
		self.serial1 = serial1
		self.serial2 = serial2

	def vote(self):
		print('\t投票コード"' + self.serial_number + '"を投票します。\n')

		# セッションを作成する
		opener = urllib.request.build_opener(
			urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))

		# 投票画面のページにアクセスし、XSRFのパラメータを取得する
		member_url = base_url + '/show?c=' + candidate_code
		response = opener.open(member_url)
		session_id = response.getheader('Set-Cookie').split(';')[0]
		vote_page_parser = VotePageParser(response)
		xsrf_param = vote_page_parser.get_xsrf_param()

        # 投票リスエストのヘッダを追加
		header = {
		    'Host': 'akb48-sousenkyo.jp',
		    'Connection': 'keep-alive',
		    'Referer': 'http://akb48-sousenkyo.jp/web/akb2015/vote/show?c=' + candidate_code,
		    'Cache-Control': 'max-age=0',
		    'Origin': 'http://akb48-sousenkyo.jp',
		    'Content-Type': 'application/x-www-form-urlencoded',
		    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
		    'X-Requested-With': 'com.android.browser',
		    'User-Agent': ' Mozilla/5.0 (Linux; Android 4.1.1; Nexus 7 Build/JRO03S) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.166 Safari/535.19',
		    'Accept-Encoding': 'gzip,deflate',
		    'Accept-Language': 'ja-JP, en-US;q=0.8',
		    'Accept-Charset': 'utf-8, iso-8859-1, utf-16, *;q=0.7',
		}
		for key, value in header.items():
			opener.addheaders.append((key, value))

		# 投票リスエストのパラメータを追加
		params = {
		    "vote_form_candidate_code": candidate_code,
		    "detect": '判定',
		    "vote_form_sys.xsrf": xsrf_param,
		    "vote_form_serial_code_1": self.serial1,
		    "vote_form_serial_code_2": self.serial2,
		}
		data = urllib.parse.urlencode(params).encode('utf-8')

		# 投票リクエストを送信する
		response = opener.open(vote_url, data, 5)

		# 投票結果を取得する
		self.status = response.code
		self.respose_body = response.read().decode('sjis')

	def save_result(self, destdir):
		result_file = destdir + '/' + str(self.status) + '_' + self.serial_number + '.html'
		f = open(result_file, 'w', encoding='utf-8')
		f.write(self.respose_body)
		f.close()

class VotePageParser(HTMLParser):
	def __init__(self, response):
		HTMLParser.__init__(self)
		self.xsrf_param = ''
		self.feed(str(response.read()))

	def handle_starttag(self, tag, attrs):
		if tag == 'input':
			attrs_dict = dict(attrs)
			if 'name' in attrs_dict and 'value' in attrs_dict and attrs_dict['name'] == xsrf_param_name:
				self.xsrf_param = attrs_dict['value']

	def get_xsrf_param(self):
		return self.xsrf_param

def read_vote_code(filename=vote_file_name):
	print('投票コードを読み込み中...')
	try:
		f = open(filename, 'r')
		lines = f.readlines()
	except IOError:
		print('投票コードファイル"' + filename + '"が開けません。\n')
		raise
	finally:
		f.close()

	# 投票コード一覧
	votecodelist = []
	for line in lines:
		splits = line.rstrip('\r\n').split(' ')
		votecodelist.append(validate_vote_code(splits))
	
	# 投票コード確認
	if len(votecodelist) == 0:
		raise Exception('投票コードが投票コードファイルに記述されていません。')

	print('投票コードの読み込み完了.')
	return votecodelist

def validate_vote_code(splits):
	if len(splits) != 2 or len(splits[0]) != 8 or len(splits[1]) != 8:
		raise Exception('投票コードファイルの形式が不正です。\n' +
				'一行ごとに、投票コードの上8桁と下8桁を" "で区切って入力して下さい。')
	return splits

if __name__ == '__main__':
	try:
		# 投票コードを読み込む
		votecodelist = read_vote_code()

		# 結果画面の保存先ディレクトリを作成
		if not os.path.exists(destdir):
			os.mkdir(destdir)

		# 投票して結果画面を保存する
		for votecode in votecodelist:
			# 投票機を作成する
			voter = Voter(candidate_code, votecode[0], votecode[1])

			# 投票する
			voter.vote()

			# 投票結果画面を保存する
			voter.save_result(destdir)

		# 投票完了
		print('投票を完了しました。\n')
	except Exception as e:
		print('ERROR: ' + str(e) + '\n')
		raise
