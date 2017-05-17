#!/usr/bin/python

from flask import Flask, request, jsonify
import websocket, time, ssl, json
from threading import Thread

class SonoffService:
	def __init__(self):
		self.ws = None
		self.ws_thread = None
		self.ws_ping_thread = None
		self.switch_status_dic = {}
		self.appid = ""
		self.apikey = ""
		self.nonce = ""
		self.at = ""
		self.imei = ""
		
	def get_switch_status(self, switch_id):
		if self.switch_status_dic.has_key(switch_id):
			return self.switch_status_dic[switch_id]
		else:
			return ""
			
	def set_switch_status(self, switch_id, status):
		self.switch_status_dic[switch_id] = status
		sequence = "%d" % (time.time() * 1000)
		string = '{"userAgent":"app","sequence":%s,"deviceid":"%s","apikey":"%s","params":{"deviceType":"normal","switch":"%s","mainSwitch":"%s"},"action":"update"}' % (sequence, switch_id, self.apikey, status, status)
		self.send(string)
		
	def start(self):
		if self.ws_thread == None:
			self.ws_thread = Thread(target=self.open)
			self.ws_thread.start()
		
		if self.ws_ping_thread == None:
			self.ws_ping_thread = Thread(target=self.ping)
			self.ws_ping_thread.start()
	
	def auth(self):
		time_stamp = time.time()
		ts = "%d" % time_stamp
		sequence = "%d" % (time_stamp * 1000)
		string = '{"appid":"%s","userAgent":"app","version":6,"nonce":"%s","apkVesrion":"1.8","os":"ios","action":"userOnline","at":"%s","imei":"%s","apikey":"%s","ts":%s,"model":"iPhone6,2","romVersion":"9.2","sequence":%s}' % (self.appid, self.nonce, self.at, self.imei, self.apikey, ts, sequence)
		self.send(string)
	
	def open(self):
		self.ws = websocket.WebSocketApp("wss://cn-long.coolkit.cc:8080/api/ws", on_message = self.on_message, on_error = self.on_error, on_close = self.on_close)
		self.ws.on_open = self.on_open
		self.ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
	
	def close(self):
		self.ws.close()
	
	def ping(self):
		while True:
			time.sleep(145)
			self.send('ping')
			
	def send(self, message):
		print "send %s" % message
		try:
			self.ws.send(message)
		except:
			pass
			
	def on_message(self, ws, message):
		print "on_message %s" % message
		dic = json.loads(message)
		if dic.has_key("action") and dic["action"] == "update":
			params = dic["params"]
			if params.has_key("switch"):
				switch_id = dic["deviceid"]
				status = params["switch"]
				self.switch_status_dic[switch_id] = status

	def on_error(self, ws, error):
		print "on_error %s" % error

	def on_close(self, ws):
		print "on_close"
		self.ws = None
		self.ws_thread = None
		time.sleep(5)
		self.start()

	def on_open(self, ws):
		self.auth()

sonoff_service = SonoffService()
app = Flask(__name__)

@app.route('/switch/<switch_id>', methods=['GET', 'POST'])
def switch_switch(switch_id):
	switch_id = switch_id.encode("ascii")
	if request.method == "POST":
		status = request.data
		sonoff_service.set_switch_status(switch_id, status)
	res = sonoff_service.get_switch_status(switch_id)
	return res

if __name__ == "__main__":
	sonoff_service.start()
	app.run(host='0.0.0.0')