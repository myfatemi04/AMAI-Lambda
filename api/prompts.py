# Prompt Management

from .db import prompts
import bson

import api.llms

class CompletionPrompt:
	def __init__(self, template: str, model_key: str = 'text-davinci-003', **model_args):
		self.template = template
		self.model_key = model_key
		self.model_args = model_args

	def __call__(self, **kwargs):
		return api.llms.openai(self.model_key, self.template.format(**kwargs), **self.model_args)

class ListPrompt(CompletionPrompt):
	def __call__(self, **kwargs):
		return extract_list_from_gpt_completion(super().__call__(**kwargs))

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

def get_prompt(prompt_id: str):
	prompt = prompts.find_one({'_id': bson.ObjectId(prompt_id)})
	if prompt is None:
		return None

	prompt.pop("_id")
	prompt_type = prompt.pop('type', 'completion')
	prompt_template = prompt.pop('template')
	prompt_model_key = prompt.pop('model_key', 'text-davinci-003')

	if prompt_type == 'completion':
		return CompletionPrompt(prompt_template, prompt_model_key, **prompt)
	elif prompt_type == 'list':
		return ListPrompt(prompt_template, prompt_model_key, **prompt)
