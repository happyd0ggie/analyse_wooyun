#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'get bug list from www.wooyun.org'

__author__ = 'deyoung_shen@msn.cn'

import urllib3
from bs4 import BeautifulSoup
import re
import random
import os
import sys
import pymysql

# mysql connection settings
HOST = '127.0.0.1'
USER = 'root'
PASSWD = 'root'
DB = 'wooyun'
PORT = 3306
CHARSET = 'utf8'

base_url = 'www.wooyun.org'
start_page_num = 1
end_page_num = None
total_bugs_num = None

# get bugs number and bugs page number
def get_num(url):
	global end_page_num
	global total_bugs_num

	http = urllib3.PoolManager()
	res = http.request('GET', url)
	if res.status == 200:
		html_page = res.data.decode('utf-8')
		soup = BeautifulSoup(html_page, 'html.parser')
		page_txt = str(soup.find_all('p', 'page')[0])
		num_txt = re.findall('[0-9]+', page_txt)
		total_bugs_num = int(num_txt[0])
		end_page_num = int(num_txt[1])
		#print(type(page_txt))
		#print(page_txt)
		#print(html_page, type(html_page))
	else:
		print('Oops, an error occured.')
		sys.exit(1)

def get_bug():
	pass

# store data to mysql
def store_data(sql):
	global HOST
	global USER
	global PASSWD
	global DB
	global PORT
	global CHARSET

	#print(sql)
	conn = pymysql.connect(host = HOST, user = USER, passwd = PASSWD, db = DB,
		port = PORT, charset = CHARSET)

	cur = conn.cursor()
	try:
		cur.execute(sql)
	except Exception as e:
		print(str(e))
	else:
		print('store data successful.')
	finally:
		conn.commit()
		cur.close()
		conn.close()

# get bugs list from wooyun.org
def get_bugs():
	# get bugs one by one page
	for i in range(start_page_num, end_page_num + 1):
		url = base_url + '/bugs/page/' + str(i)
		http = urllib3.PoolManager()
		res = http.request('GET', url)
		if res.status == 200:
			submit_date = []
			bug_url = []
			bug_title = []
			comments = []
			attentions = []
			whitehats = []

			html_page = res.data.decode('utf-8')
			soup = BeautifulSoup(html_page, 'html.parser')
			bugs = soup.find_all('table', 'listTable')[0].find_all('tbody')[0]

			# find submit date
			for th in bugs.find_all('th'):
				for datetime in re.findall('[0-9]{4}-[0-9]{2}-[0-9]{2}', str(th)):
					submit_date.append(datetime)

			# find bug_url and bug_title
			links = bugs.find_all('a')
			
			for link in links:
				href = link.get('href')
				# get bug url and bug title
				if href.startswith('/bugs/wooyun') and \
				not href.endswith('comment'):
					bug_url.append('http://www.wooyun.org' + href)
					bug_title.append(link.get_text())
				# get whitehats
				if href.startswith('/whitehats/'):
					whitehats.append(link.get_text())
				# get comments and attentions
				if href.endswith('comment'):
					comments.append(link.get_text().split('/')[0])
					attentions.append(link.get_text().split('/')[1])

			# store to mysql and write to file
			for i in range(len(bug_url)):
				print(bug_url[i], end = '\t')
				print(bug_title[i])
				sql = 'INSERT INTO bugs(`submit_date`, `bug_title`, `bug_url`,\
				`comments`, `attentions`, `whitehats`) VALUES("%s", "%s", "%s", \
				"%s", "%s", "%s")' % (submit_date[i], bug_title[i], bug_url[i],
					comments[i], attentions[i], whitehats[i])
				store_data(sql)
				record = bug_url[i] + '###' + bug_title[i] + '###' + comments[i] \
				+ '###' + attentions[i] + '###' + whitehats[i] + '\n'
				with open('bugs.dat', 'at') as f:
					f.write(record)

def main():
	get_num(base_url + '/bugs/page/1')
	get_bugs()

if __name__ == '__main__':
	main()
	#print('total bugs number:', total_bugs_num)
	#print('total pages number:', end_page_num)