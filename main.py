from credentials import ACCESS_TOKEN, GROUP_ID, BOT_ID
import requests
import json
import time


class Bot:
	def __init__(self):
		self.id = BOT_ID
		self.token = ACCESS_TOKEN
		self.group_id = None

	def register(self, name, group):
		url = f'https://api.groupme.com/v3/bots?token={self.token}'
		data = {"bot": {"name": name, "group_id": str(group)}}

		r = requests.post(url, data=json.dumps(data)).content
		self.id = json.loads(r)['response']['bot']['bot_id']

	def post(self, message):
		url = 'https://api.groupme.com/v3/bots/post'
		data = {"bot_id": self.id, "text": message}
		requests.post(url, data=json.dumps(data))

	def get_messages(self, group=GROUP_ID, limit=100):
		base_url = 'https://api.groupme.com/v3'
		url = f'{base_url}/groups/{group}/messages?token={self.token}'

		r = json.loads(requests.get(url).content)
		return r['response']['messages']

	def run(self, group=GROUP_ID, limit=100):
		messages = self.get_messages(group, limit)
		# determine if we need to count votes
		# this will happen if there's a /votestop but not a more recent Results

		# find most recent votestop
		for i, msg in enumerate(messages):
			if msg['text'] == '/votestop':
				# found /votestop in position i, so now we need to go through
				# everything "after" this message (earlier in the list) and find if there's a result
				# post
				for msg_ in messages[:i]:
					if msg_['text'].startswith('Results:'):
						# we found the results, so we're done
						break
				else:
					# no results, so we need to do that
					self.count_votes(group)
		else:
			# no votestop, so we don't need to do anything
			pass

	def count_votes(self, group=GROUP_ID):
		votestop, votestart = None, None
		# find votestop and votestart
		messages = self.get_messages()
		for i, msg in enumerate(messages):
			if msg['text'] == '/votestop':
				votestop = i
			elif msg['text'] == '/votestart':
				votestart = i

			if votestop is not None and votestart is not None:
				break

		relevant_messages = messages[votestop:votestart]

		y = sum(1 for msg in relevant_messages if msg['text'] == '/yes')
		n = sum(1 for msg in relevant_messages if msg['text'] == '/no')
		a = sum(1 for msg in relevant_messages if msg['text'] == '/abstain')

		self.post(f'Results: {y}-{n} (with {a} abstention{"s" if a != 1 else ""})')


votebot = Bot()
while True:
	votebot.run()
	time.sleep(15)
