# Prompt Management

from db import prompts
import bson

import requests
import os
from apis import openai, huggingface

class CompletionPrompt:
	def __init__(self, template: str, model_key: str = 'text-davinci-003', **model_args):
		self.template = template
		self.model_key = model_key
		self.model_args = model_args

	def __call__(self, **kwargs):
		formatted = self.template.format(**kwargs)

		return gpt3(self.model_key, formatted, **self.model_args)

class ListPrompt(CompletionPrompt):
	def __call__(self, **kwargs):
		completion = super().__call__(**kwargs)

		return extract_list_from_gpt_completion(completion)

def extract_list_from_gpt_completion(completion: str):
	import re

	results = []
	next_is_result = False
	for line in completion.splitlines():
		line = line.strip()

		if len(line) == 0:
			continue

		if next_is_result:
			results.append(line)
			next_is_result = False
			continue

		if re.match(r'^\d+\. .+$', line):
			phrase = line[line.index('.') + 1:].strip()
			results.append(phrase)
		elif re.match(r'^\d+\.$', line):
			next_is_result = True
	
	return results

def gpt3(model_key, prompt: str, temperature=0.7, max_tokens=120, stop=None) -> str:
	response = requests.post('https://api.openai.com/v1/completions', json={
		'model': model_key,
		'prompt': prompt,
		'temperature': temperature,
		'max_tokens': max_tokens,
		'top_p': 1,
		'frequency_penalty': 0,
		'presence_penalty': 0,
	}, headers={
		'Authorization': 'Bearer ' + os.environ['OPENAI_API_KEY'],
		'Content-Type': 'application/json',
	})
	response = response.json()

	return response['choices'][0]['text']

def get_prompt(prompt_id: str):
	prompt = prompts.find_one({'_id': bson.ObjectId(prompt_id)})
	if prompt is None:
		return None

	prompt_type = prompt.pop('type', 'completion')
	prompt_template = prompt.pop('template')
	prompt_model_key = prompt.pop('model_key', 'text-davinci-003')

	if prompt_type == 'completion':
		return CompletionPrompt(prompt_template, prompt_model_key, **prompt)
	elif prompt_type == 'list':
		return ListPrompt(prompt_template, prompt_model_key, **prompt)
