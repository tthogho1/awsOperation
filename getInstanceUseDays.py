import subprocess
import json

# Execute an AWS CLI command to describe instances
PROFILE = " --profile company"
#PROFILE = ""
getInstancelist = "aws ec2 describe-instances" + PROFILE + " --output json"
cpuUsedList = 'aws cloudwatch get-metric-statistics' + PROFILE + ' --metric-name CPUUtilization --start-time {0}-{1} --end-time {0}-{2} --period 86400 --namespace AWS/EC2 --statistics Sum --dimensions Name=InstanceId,Value={3}'

monthTimeList=[
    ["01-01T00:00:00Z","01-31T23:59:59Z"],
    ["02-01T00:00:00Z","02-28T23:59:59Z"],
    ["03-01T00:00:00Z","03-31T23:59:59Z"],
    ["04-01T00:00:00Z","04-30T23:59:59Z"],
    ["05-01T00:00:00Z","05-31T23:59:59Z"],
    ["06-01T00:00:00Z","06-30T23:59:59Z"],
    ["07-01T00:00:00Z","07-31T23:59:59Z"],
    ["08-01T00:00:00Z","08-31T23:59:59Z"],
    ["09-01T00:00:00Z","09-30T23:59:59Z"],
    ["10-01T00:00:00Z","10-31T23:59:59Z"],
    ["11-01T00:00:00Z","11-30T23:59:59Z"],
    ["12-01T00:00:00Z","12-31T23:59:59Z"]
]

TagDict = {}
PlatFormDict = {}

def getUsedDaysInMonth(year,startDay,endDay,instanceId):
    cmd = cpuUsedList.format(year,startDay,endDay,instanceId)
    #print(cmd)
    cmdArray = cmd.split(" ")
    result = subprocess.run(cmdArray, stdout=subprocess.PIPE)
    return json.loads(result.stdout.decode())

def calculateDataPoints(dataPoints):
    if len(dataPoints) == 0:
        return {"UseDays":0,"cpuTotal":0}

    totalCpuUsed = 0
    for dataPoint in dataPoints:
        totalCpuUsed = totalCpuUsed + dataPoint['Sum']

    return {"UseDays":len(dataPoints),"cpuTotal":round(totalCpuUsed)}

def getInstanceName(instanceId):
    for tag in TagDict[instanceId]:
        if tag['Key'] == 'Name':
            return tag['Value']
    return ""

def getInstanceCost(instanceId):
    for tag in TagDict[instanceId]:
        if tag['Key'] == 'Cost':
            return tag['Value']
    return ""

def getInstancePlatform(instanceId):
    return PlatFormDict[instanceId]

def  printEachInstanceData(instanceDic):
    editLine = ""
    for instanceId in instanceDic:
        editLine = editLine + instanceId + "," + getInstanceName(instanceId) + "," + getInstanceCost(instanceId) + "," + getInstancePlatform(instanceId)
        monthDataList = instanceDic[instanceId]
        for monthData in monthDataList:
            editLine = editLine + "," + str(monthData['UseDays'])     
        print(editLine) # print instance id and used days in month
        
        editLine = instanceId + "," + getInstanceName(instanceId) + "," + getInstanceCost(instanceId) + "," + getInstancePlatform(instanceId)
        for monthData in monthDataList:
            editLine = editLine + "," + str(monthData['cpuTotal'])
        print(editLine) # print instance id and cpu total in month
#
# meain function
#
cmdArray = getInstancelist.split(" ")
#print( len(cmdArray))
result = subprocess.run(cmdArray, stdout=subprocess.PIPE)

# Parse the JSON output
InstanceData = json.loads(result.stdout.decode())

# Print the instance IDs
for reservation in InstanceData['Reservations']:

    instanceDic = {}
    for instance in reservation['Instances']:
        # print(instance['InstanceId'])
        instanceId = instance['InstanceId']
        TagDict[instanceId] = instance['Tags']
        PlatFormDict[instanceId] = instance.get('Platform',"?")
        # get cpu used days in month
        monthDataLIst = []
        for monthTime in monthTimeList:
            UsedData = getUsedDaysInMonth("2022",monthTime[0],monthTime[1],instanceId)            
            dataPoints = UsedData['Datapoints']
            monthData = calculateDataPoints(dataPoints)
            monthDataLIst.append(monthData)
        
        #print(monthDataLIst)
        instanceDic[instanceId] = monthDataLIst
    
    printEachInstanceData(instanceDic)
