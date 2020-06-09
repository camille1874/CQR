import re
p = "replace ref , {entity\\d+\\.\\d+}"
action = "replace ref , {entity1.0} {entity2.0}"
#action = "replace {entity0.0} , {entity2.0}"
#p = "replace {entity\\d+\\.\\d+} , {entity\\d+\\.\\d+}" 
if re.match(p, action):
	print("here")
