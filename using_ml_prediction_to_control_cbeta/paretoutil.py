import os
def OpenFile(File,SkipLines=0):
	with open(File,'r') as f:
		for j in range(SkipLines):
			blah=f.readline() #skip any headers if present
		lines=f.readlines()
	f.close()
	return lines
def MakeDecDic(File):
	lines=OpenFile(File)
	DecDic={}
	for line in lines:
		line=line.split()
		DecDic[line[0]]=[float(line[2]),float(line[3])] #Keyword=[min,max]
	return DecDic
def MakeObjDic(File):
	lines=OpenFile(File)
	ObjDic={}
	for line in lines:
		line=line.split()
		ObjDic[line[0]]=line[1]
	return ObjDic
def MakeConDic(File):
	lines=OpenFile(File)
	ConDic={}
	for line in lines:
		line=line.split()
		ConDic[line[0]]={line[1]:float(line[2])} #constrain variable= {type of constraint: value} (potentially not general enough)
	return ConDic
def MakeFileDic(FileName=[],AddPath='../'):
    '''
    FileName= Should be a path leading to var_param
    AddPath= local path from where you execute python to where main directory is (i.e. directory where ./how_to_run.txt was executed)
    returns a dictionary of file paths from var_param
    '''
    #if not FileName:FileName='../optconf/var_param'
    if not FileName:FileName=AddPath+'optconf/var_param'
    lines=OpenFile(FileName)
    #These are files set in var_param
    FileDic={'decision_variables_file':'','objectives_file':'','constraints_file':'','initial_data_file':'','outputfile':''}
    for line in lines:
        CurLine=line.split()
        if len(CurLine)>0:
            for k in FileDic:
                if CurLine[0]==k:FileDic[k]=AddPath+CurLine[1]
    return FileDic




def GetAFront(FrontNumber,Skiplines=0,AddPath='../'): #better name would be GetAnIndividual, but too late for that...
	'''
	FrontNumber=based on the order the point appeared in the .out file
	creates a dictionary containing all variables used to compute point on Pareto front
	AddPath= local path from where you execute python to where main directory is (i.e. directory where ./how_to_run.txt was executed)
	'''
	FileDic=MakeFileDic(AddPath=AddPath)
        ####
	ParetoFile=FileDic['outputfile']
	DecFile=FileDic['decision_variables_file']
	DecDic=MakeDecDic(DecFile)
	ObjFile=FileDic['objectives_file']
	ObjDic=MakeObjDic(ObjFile)
	ConFile=FileDic['constraints_file']
	ConDic=MakeConDic(ConFile)
	#####
	lines=OpenFile(ParetoFile,SkipLines=2)
	FrontLine=lines[FrontNumber].split()
	FrontDic={}
	ind=0
	for k in DecDic:
		FrontDic[k]=['D',float(FrontLine[ind])]
		ind=ind+1
	for k in ObjDic:
		FrontDic[k]=['O',float(FrontLine[ind])]
		ind=ind+1
	for k in ConDic:
		FrontDic[k]='C'
	return FrontDic
def DummyFront(AddPath='../'): #creates a FrontDic just like GetAFront but with holder values
	'''
	AddPath= local path from where you execute python to where main directory is (i.e. directory where ./how_to_run.txt was executed)
	'''
	FileDic=MakeFileDic(AddPath=AddPath)
        ####
	ParetoFile=FileDic['outputfile']
	DecFile=FileDic['decision_variables_file']
	DecDic=MakeDecDic(DecFile)
	ObjFile=FileDic['objectives_file']
	ObjDic=MakeObjDic(ObjFile)
	ConFile=FileDic['constraints_file']
	ConDic=MakeConDic(ConFile)
	#####
	#lines=OpenFile(ParetoFile,SkipLines=2)
	#FrontLine=lines[FrontNumber].split()
	FrontDic={}
	ind=0
	for k in DecDic:
		FrontDic[k]=['D',float(1e89)] #these are holder values
		ind=ind+1
	for k in ObjDic:
		FrontDic[k]=['O',float(1e89)]
		ind=ind+1
	for k in ConDic:
		FrontDic[k]='C'
	return FrontDic

def MakeFrontFile(FileName,FrontNumber):
	'''
	creates a file that can be used with func_eval.py
	'''
	try: shutil.rmtree(FileName)
	except: pass
	FrontDic=GetAFront(FrontNumber)
	with open(FileName,"w+") as f:
		f.write('ID   id_number   0 \n')
		f.write('NODE  node_name   all.q \n')
		f.write('FILE_CLEANUP   F   1 \n')
		#f.write('TEMPLATE_DIR   P '+TemplateDir+ ' \n')
		#f.write('TEMP_DIR   P '+ TempDir+ ' \n')
		for k,v in FrontDic.items():
			if v!='C':
				if v[0]=='D':
					f.write(k+' '+v[0]+ ' '+ str(v[1])+"\n")
				if v[0]=='O':
					f.write(k+' '+v[0]+"\n")
			if v=='C':
				f.write(k+' C\n')
		f.close()
def MakeFrontFileFromFront(FileName,FrontDic,ID_number=0,FileClean=1):
	'''
	creates a file that can be used with func_eval.py
	'''
	try: shutil.rmtree(FileName)
	except: pass
	with open(FileName,"w+") as f:
		f.write('ID   id_number ' + str(ID_number)+' \n')
		f.write('NODE  node_name   all.q \n')
		#f.write('FILE_CLEANUP   F   1 \n')
		f.write('FILE_CLEANUP   F '  +str(FileClean) +'\n')
		#f.write('TEMPLATE_DIR   P '+TemplateDir+ ' \n')
		#f.write('TEMP_DIR   P '+ TempDir+ ' \n')
		for k,v in FrontDic.items():
			if v!='C':
				if v[0]=='D':
					f.write(k+' '+v[0]+ ' '+ str(v[1])+"\n")
				if v[0]=='O':
					f.write(k+' '+v[0]+"\n")
			if v=='C':
				f.write(k+' C\n')
		f.close()
def GetParetoCol(File,ColName,FrontDic):
	lines=OpenFile(File,SkipLines=2)
	ColInd=0
	Col=[]
	FoundColumn=False
	for k in FrontDic:
		if k==ColName:
			FoundColumn=True
			#print('found it')
			break
		ColInd=ColInd+1
	CurLine=0
	for line in lines:
		line=line.split()
		if line !=[]:
			Col.append(float(line[ColInd]))
			CurLine=CurLine+1
	if FoundColumn==False:
		print('Warning: Column not found')
		return []
	else:
		return Col
def GetParetoFront(AddPath='../'):
	FileDic=MakeFileDic(AddPath=AddPath)
	PareFile=FileDic['outputfile']
	ObjFile=FileDic['objectives_file']
	ObjDic=MakeObjDic(ObjFile)
	FrontDic=GetAFront(1)
	NumObjs=len(ObjDic)
	ObjArray=[]
	ObjNames=[]
	for k in ObjDic:
		ObjCol=GetParetoCol(PareFile,k,FrontDic)
		ObjArray=ObjArray+[ObjCol]
		ObjNames=ObjNames+[k]
	return ObjNames,ObjArray

def GetObjsFromRun(RunFile,AddPath='../'): #same as GetParetoFront but can be directed to RUN01_his if needed
	FileDic=MakeFileDic(AddPath=AddPath)
	PareFile=RunFile
	ObjFile=FileDic['objectives_file']
	ObjDic=MakeObjDic(ObjFile)
	try:
		FrontDic=GetAFront(1,AddPath=AddPath)
	except:
		FrontDic=DummyFront(AddPath=AddPath)
	NumObjs=len(ObjDic)
	ObjArray=[]
	ObjNames=[]
	for k in ObjDic:
		ObjCol=GetParetoCol(PareFile,k,FrontDic)
		ObjArray=ObjArray+[ObjCol]
		ObjNames=ObjNames+[k]
	return ObjNames,ObjArray


