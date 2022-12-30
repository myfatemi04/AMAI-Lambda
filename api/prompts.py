# Prompt Management

from .db import prompts
import bson

import api.llms

class MissingVariableException(Exception):
	def __init__(self, variable: str):
		self.variable = variable
		super().__init__("Missing variable " + variable)

class CompletionPrompt:
	def __init__(self, template: str, model_key: str = 'text-davinci-003', generation_params = {}, variables = []):
		self.template = template
		self.model_key = model_key
		self.generation_params = generation_params
		self.variables = variables

	def __call__(self, **kwargs):
		print(f"Calling prompt with {kwargs=} and {self.generation_params=}")

		for variable in self.variables:
			if variable not in kwargs:
				raise MissingVariableException(f"Missing variable {variable} in {kwargs}")

		return api.llms.openai(self.model_key, self.template.format(**kwargs), **self.generation_params)

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
	template = prompt.pop('template')
	model_key = prompt.pop('model_key', 'text-davinci-003')
	variables = prompt.pop('variables', {})
	generation_params = prompt.pop('generation_params', {})

	if prompt_type == 'completion':
		return CompletionPrompt(template, model_key, generation_params)
	elif prompt_type == 'list':
		return ListPrompt(template, model_key, generation_params)
