def genMsg(ifSuccess, msg):
   result = {}
   result["success"] = bool(ifSuccess)
   result["msg"] = msg
   return result

def genData(ifSuccess, data):
   result = {}
   result["success"] = bool(ifSuccess)
   result["data"] = data
   return result