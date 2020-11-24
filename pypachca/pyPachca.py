import requests
import os.path
import typing
import re
from fuzzywuzzy import process as fwprocess
from typing import List


class PachcaOAuth:
	def __init__(self, client_id: str, client_secret: str, redirect_uri: str, refresh_file: str = ".refresh_token",
				 code: str = None):
		self.api_url = "https://api.pachca.com/api/shared/v1"
		self.client_id = client_id
		self.client_secret = client_secret
		self.refresh_file = refresh_file
		self.redirect_uri = redirect_uri
		self.code = code

	def _save_refresh_token(self, token: str):
		with open(self.refresh_file, "w+") as refresh:
			refresh.write(token)

	def _get_access_from_request(self, auth_type: str):
		data = {
			"client_id": self.client_id,
			"client_secret": self.client_secret,
			"grant_type": auth_type,
			"redirect_uri": self.redirect_uri
		}
		if auth_type == "authorization_code":
			data["code"] = self.code
		elif auth_type == "refresh_token":
			data["refresh_token"] = self.refresh_token
		else:
			raise ValueError(f"auth_type должно быть 'authorization_code' или 'refresh_token'")

		response = requests.post(f"{self.api_url}/oauth/token", json=data)

		if response.status_code // 100 == 2:
			response = response.json()
			self._save_refresh_token(response["refresh_token"])
			return response["access_token"]
		elif response.status_code // 100 == 4:
			response = response.json()
			raise ValueError(f"{response['error']} - {response['error_description']}")
		else:
			raise ValueError(f"{response.text}")

	def _get_access_token(self):
		if os.path.exists(self.refresh_file):
			return self._get_access_from_request(auth_type="refresh_token")
		else:
			if not self.code:
				self.code = input("Введите authorization_code\n>>> ")
			if re.match("[a-zA-Z0-9-_]{43}", self.code):
				return self._get_access_from_request(auth_type="authorization_code")
			else:
				raise ValueError(
					"code должен состоять из латинских символов верхнего и нижнего регистра, цифр и знаков '-'")

	@property
	def access_token(self):
		return self._get_access_token()

	@property
	def auth_headers(self):
		return {'Authorization': f'Bearer {self.access_token}'}

	@property
	def refresh_token(self):
		with open(self.refresh_file, "r") as refresh:
			return refresh.read()


class Stage:
	def __init__(self, stage: dict):
		self.id: int = stage["id"]
		self.name: str = stage["name"]
		self.sort: int = int(stage["sort"])
		self.raw: dict = stage

	def __str__(self):
		tmp_dict = {"id": self.id, "name": self.name, "sort": self.sort}
		return str(tmp_dict)

	def __repr__(self):
		return f"<{self.name} #{self.id} sort: {self.sort}>"


class Funnel:
	def __init__(self, funnel: dict):
		self.id: int = funnel["id"]
		self.name: str = funnel["name"]
		self.stages: List[Stage] = [Stage(stage) for stage in funnel["stages"]]
		self.raw: dict = funnel

	def __str__(self):
		tmp_dict = {"id": self.id, "name": self.name, "stages": self.stages}
		return str(tmp_dict)

	def __repr__(self):
		return f"<{self.name} #{self.id} {self.stages}>"


class Property:
	def __init__(self, property_data: dict):
		self.id: int = property_data["id"]
		self.name: str = property_data["name"]
		self.data_type: str = property_data["data_type"]
		self.raw: dict = property_data
		self.value = property_data["value"] if "value" in property_data else None


class User:
	def __init__(self, user: dict):
		self.id: int = user["id"]
		self.first_name: str = user["first_name"]
		self.last_name: str = user["last_name"]
		self.nickname: str = user["nickname"]
		self.email: str = user["email"]
		self.phone_number: str = user["phone_number"]
		self.department: str = user["department"]
		self.role: str = user["role"]
		self.suspended: bool = user["suspended"]
		self.raw: dict = user

	@property
	def full_name(self):
		return f"{self.first_name} {self.last_name}"

	def __repr__(self):
		return f"<{self.full_name} @{self.nickname} #{self.id}>"


class Organisation:
	def __init__(self, organisation: dict):
		self.id: int = organisation["id"]
		self.name: str = organisation["name"]
		self.inn: str = organisation["inn"]
		self.properties: List[Property] = [Property(property_data) for property_data in organisation["custom_properties"]]
		self.raw: dict = organisation


class Client:
	def __init__(self, client: dict):
		self.id: int = client["id"]
		self.client_number: int = client["client_number"]
		self.full_name: str = client["full_name"]
		self.owner_id: int = client["owner_id"]
		self.created_at: str = client["created_at"]
		self.phones: List[str] = client["phones"]
		self.emails: List[str] = client["emails"]
		self.address: str = client["address"]
		self.organization_id: int = client["organization_id"]
		self.additional: str = client["additional"]
		self.list_tags: List[str] = client["list_tags"]
		self.properties: List[Property] = [Property(property_data) for property_data in client["custom_properties"]]
		self.raw: dict = client

	def __repr__(self):
		return f"<{self.full_name} @{self.client_number} #{self.id}>"


class Task:
	def __init__(self, task: dict):
		self.id: int = task["id"]
		self.kind: str = task["kind"]
		self.content: str = task["content"]
		self.due_at: str = task["due_at"]
		self.priority: int = task["priority"]
		self.user_id: int = task["user_id"]
		self.status: str = task["status"]
		self.created_at: str = task["created_at"]
		self.performer_ids: dict = task["[performer_id"]
		self.raw = task


class Deal:
	def __init__(self, deal: dict, pachca=None):
		self.id: int = deal["id"]
		self.owner_id: int = deal["owner_id"]
		self.created_at: str = deal["created_at"]
		self.name: str = deal["name"]
		self.client_id: int = deal["client"]
		self.stage_id: int = deal["stage_id"]
		self.cost: int = deal["cost"]
		self.state: str = deal["state"]
		self.properties: List[Property] = [Property(property_data) for property_data in deal["custom_properties"]]
		self.raw: dict = deal


class Message:
	def __init__(self, message: dict):
		self.id: int = message["id"]
		self.entity_type: str = message["entity_type"]
		self.entity_id: int = message["entity_id"]
		self.content: str = message["content"]
		self.user_id: int = message["user_id"]
		self.created_at: str = message["created_at"]
		self.raw: dict = message


class Pachca:
	def __init__(self, client_id: str, client_secret: str, redirect_uri: str = "https://app.pachca.com",
				 refresh_file: str = ".refresh_token", code: str = None):
		self.OAuth = PachcaOAuth(client_id, client_secret, redirect_uri, refresh_file, code)
		self.api_url = "https://api.pachca.com/api/shared/v1"
		self.auth = self.OAuth.auth_headers

	@property
	def new_auth(self):
		new = self.OAuth.access_token
		self.auth = new
		return new

	def _make_requests(self, method: str, uri: str, data: dict = None):
		if method == "GET":
			response = requests.get(f"{self.api_url}/{uri}", headers=self.auth)
			if response.status_code == 401:
				response = requests.get(f"{self.api_url}/{uri}", headers=self.new_auth)
		elif method == "POST":
			response = requests.post(f"{self.api_url}/{uri}", headers=self.auth, json=data)
			if response.status_code == 401:
				response = requests.post(f"{self.api_url}/{uri}", headers=self.new_auth, json=data)
		else:
			raise ValueError(f"method должно быть GET или POST")
		return response

	def funnels(self):
		response = self._make_requests("GET", "funnels")
		if response.status_code // 100 == 2:
			return [Funnel(funnel) for funnel in response.json()["data"]]
		elif response.status_code // 100 in [4, 5]:
			raise ValueError(f"{response.text}")

	def custom_properties(self, entity):
		allows = ["Organization", "Client", "Deal", "Организация", "Клиент", "Сделка"]
		best = fwprocess.extract(entity, allows, limit=1)[0]
		if best[1] > 70:
			entity = {
				"Organization": "Organization", "Организация": "Organization",
				"Clients": "Clients", "Клиент": "Clients",
				"Deals": "Deals", "Сделка": "Deals"}[best[1]]
			response = self._make_requests("GET", f"custom_properties?entity_type={entity}")
			if response.status_code // 100 == 2:
				return [Property(property_data) for property_data in response.json()["data"]]
			else:
				raise ValueError(f"{response.text}")
		else:
			raise ValueError(f"entity должно быть 'Organization', 'Client' или 'Deal', вы же ввели какое-то говно…")

	def users(self):
		response = self._make_requests("GET", "users")
		if response.status_code // 100 == 2:
			return [User(user) for user in response.json()["data"]]
		elif response.status_code // 100 in [4, 5]:
			raise ValueError(f"{response.text}")

	def create_organisation(self, name: str = None, inn: str = None, **properties):
		if any([name, inn]):
			data = {}
			if name:
				data["name"] = name
			if inn:
				data["inn"] = inn
			if properties:
				data["custom_properties"] = []
				for prop_id, value in properties.items():
					data["custom_properties"].append({"id": int(prop_id), "value": value})
			response = self._make_requests("POST", "organizations", data={"organization": data})
			if response.status_code // 100 == 2:
				return Organisation(response.json()["data"])
			elif response.status_code // 100 in [4, 5]:
				raise ValueError(f"{response.text}")
		else:
			raise AttributeError("Не указано ни один идентификатор организации (name, inn)")

	def clients(self, filters: typing.Union[tuple, List[tuple]] = None, union: str = None, sort: tuple = None,
				per: int = 25, page: int = 1):
		queries = []
		if filters:
			if type(filters) is tuple:
				filters = [filters]
			for one_filter in filters:
				queries.append(f"filter[{one_filter[0]}][{one_filter[1]}]={one_filter[2]}")
		if union:
			queries.append(f"union={union}")
		if sort:
			queries.append(f"sort[{sort[0]}]")
		queries.append(f"per={per}&page={page}")
		response = self._make_requests("GET", f"clients?{'&'.join(queries)}")
		if response.status_code // 100 == 2:
			return [Client(client) for client in response.json()["data"]]
		elif response.status_code // 100 in [4, 5]:
			raise ValueError(f"{response.text}")

	def create_client(self,
					  full_name: str,
					  phones: typing.Union[int, str, list] = None,
					  emails: typing.Union[int, str, list] = None,
					  address: str = None,
					  organization_id: int = None,
					  additional: str = None,
					  tags: typing.Union[str, list] = None,
					  **properties):
		data = {"full_name": full_name}
		if phones:
			data["phones"] = phones if type(phones) is list else [phones]
		if emails:
			data["emails"] = emails if type(emails) is list else [emails]
		if address:
			data["address"] = address
		if organization_id:
			data["organization_id"] = organization_id
		if additional:
			data["additional"] = additional
		if tags:
			data["list_tags"] = tags if type(tags) is list else [tags]
		if properties:
			data["custom_properties"] = []
			for prop_id, value in properties.items():
				data["custom_properties"].append({"id": int(prop_id), "value": value})
		response = self._make_requests("POST", "clients", data={"client": data})
		if response.status_code // 100 == 2:
			return Client(response.json()["data"])
		elif response.status_code // 100 in [4, 5]:
			raise ValueError(f"{response.text}")

	def create_task(self, kind, content: str = None, due_at: typing.Union[str, int] = None, priority: int = 1,
					performer_ids: typing.Union[int, list] = None):
		if kind in ["call", "meeting", "reminder", "event", "email"]:
			data = {
				"kind": kind,
				"priority": priority
			}
			if content:
				data["content"] = content
			if due_at:
				data["due_at"] = due_at
			if performer_ids:
				data["performer_ids"] = performer_ids if type(performer_ids) is list else [performer_ids]
			response = self._make_requests("POST", "tasks", data={"task": data})
			if response.status_code // 100 == 2:
				return response.json()["data"]
			elif response.status_code // 100 in [4, 5]:
				raise ValueError(f"{response.text}")

	def create_deal(self, name: str, client_id: int, stage_id: typing.Union[int, str] = None, cost: int = 0,
					properties: typing.Union[list, dict] = None,
					note: typing.Union[dict, str] = None):
		if not type(stage_id) is int:
			funnels = self.funnels()
			if stage_id is None:
				if len(funnels) == 1:
					stage_id = funnels[0].stages[0].id
			elif type(stage_id) is str:
				stages = []
				for funnel in funnels:
					for stage in funnel.stages:
						stages.append(f"{stage.name}#{stage.id}")
				stage_id = int(fwprocess.extract(stage_id, stages, limit=1)[0][0].split("#")[1])
		data = {
			"name": name,
			"client_id": client_id,
			"stage_id": stage_id,
			"cost": cost
		}
		if properties:
			data["custom_properties"] = properties if type(properties) is list else [properties]
		if note:
			data["note"] = note if type(note) is dict else {"content": note}
		response = self._make_requests("POST", "deals", data={"deal": data})
		if response.status_code // 100 == 2:
			return response.json()["data"]
		elif response.status_code // 100 in [4, 5]:
			raise ValueError(f"{response.text}")

	def update_deal(self, id: int, name: str = None, stage_id: typing.Union[int, str] = None,
					cost: int = None, state: str = None, properties: typing.Union[list, dict] = None):
		if any([name, stage_id, cost, state, properties]):
			data = dict()
			if name:
				data["name"] = name
			if stage_id:
				if type(stage_id) is str:
					stages = []
					funnels = self.funnels()
					for funnel in funnels:
						for stage in funnel.stages:
							stages.append(f"{stage.name}#{stage.id}")
					stage_id = int(fwprocess.extract(stage_id, stages, limit=1)[0][0].split("#")[1])
				data["stage_id"] = stage_id
			if cost:
				data["cost"] = cost
			if state:
				data["state"] = state
			if properties:
				data["custom_properties"] = properties if type(properties) is list else [properties]
			response = self._make_requests("PUT", uri=f"deals/{id}", data={"deal": data})
			if response.status_code // 100 == 2:
				return response.json()["data"]
			elif response.status_code // 100 in [4, 5]:
				raise ValueError(f"{response.text}")
		else:
			AttributeError("Не указано ни одно обновляемое значение")

	def create_message(self, entity_id: int, content: str, entity_type: str = "Deal"):
		data = {
			"entity_type": entity_type,
			"entity_id": entity_id,
			"content": content
		}
		response = self._make_requests("POST", "messages", data={"message": data})
		if response.status_code // 100 == 2:
			return response.json()["data"]
		elif response.status_code // 100 in [4, 5]:
			raise ValueError(f"{response.text}")
