#-*- coding:utf-8 -*-
import urllib3
import requests
import json
import io
import pandas as pd
import sqlite3
from PIL import Image

def load_symp_dataset():
    global symptoms_OPH_list,symptoms_NS_list,symptoms_OS_list,symptoms_IM_list,symptoms_DER_list,symptoms_ENT_list
    global Point
    df = pd.read_excel('증상별 병원 선택.xlsx')

    symptoms_OPH_list = [] # 안과 증상
    symptoms_NS_list = []  # 신경외과 증상
    symptoms_OS_list = []  # 정형외과 증상
    symptoms_IM_list = []  # 내과 증상
    symptoms_DER_list = [] # 피부과 증상
    symptoms_ENT_list = [] # 이비인후과 증상

    symptoms_OPH_list_tmp = df['안과'].to_list()
    symptoms_OPH_list = [x for x in symptoms_OPH_list_tmp if pd.isnull(x) == False]

    symptoms_NS_list_tmp = df['신경외과'].to_list()
    symptoms_NS_list = [x for x in symptoms_NS_list_tmp if pd.isnull(x) == False]

    symptoms_OS_list_tmp = df['정형외과'].to_list()
    symptoms_OS_list = [x for x in symptoms_OS_list_tmp if pd.isnull(x) == False]

    symptoms_IM_list_tmp = df['내과'].to_list()
    symptoms_IM_list = [x for x in symptoms_IM_list_tmp if pd.isnull(x) == False]

    symptoms_DER_list_tmp = df['피부과'].to_list()
    symptoms_DER_list = [x for x in symptoms_DER_list_tmp if pd.isnull(x) == False]

    symptoms_ENT_list_tmp = df['이비인후과'].to_list()
    symptoms_ENT_list = [x for x in symptoms_ENT_list_tmp if pd.isnull(x) == False]

    Point = {'안과' : 0, '신경외과' : 0 , '정형외과' : 0 , '내과' : 0 , '피부과' : 0 , '이비인후과' : 0}

def get_response(mytext):
    global response
    openApiURL = "http://aiopen.etri.re.kr:8000/WiseNLU_spoken" 
        
    accessKey = "e6fe0ef4-1806-4407-91c1-fd2f51737567"
    analysisCode = "ner"
    print(f"yout sentence : {mytext}")
    text = mytext

    requestJson = {  
        "argument": {
            "text": text,
            "analysis_code": analysisCode
        }
    }

    http = urllib3.PoolManager()
    response = http.request(
        "POST",
        openApiURL,
        headers={"Content-Type": "application/json; charset=UTF-8", "Authorization" :  accessKey},
        body=json.dumps(requestJson)
    )


def analysis_symp():
    global max_point_hospital
    # print(str(response.data,"utf-8"))
    # response.data 는 response datasegment의 대한 json 파일로 이루어져 있음 

    # json.load 는 json 데이터의 문자열 해석 / 딕셔트리 리스트 반환 
    # -> print 시 return key 와 return_object key 확인
    response_data = json.loads(response.data)
    # return_object 는 딕셔너리 response_data 에서 'return_object' ket만 추출
    return_object = response_data['return_object']
    return_object_sentence = return_object['sentence']
    #print(return_object_sentence)
    sentence_NE = return_object_sentence[0]['NE']
    target_list = list()
    for item in sentence_NE:
        if(item['type'] == 'TMM_DISEASE' or item['type'] == 'TM_CELL_TISSUE' or item['type'] == 'AM_PART'):
            target_list.append(item['text'])

    print(target_list)
    print(symptoms_ENT_list)
    for item in target_list:
        print(item)
        for symp1 in symptoms_OPH_list:
            if item in symp1:
                Point['안과'] += 1
                break
        for symp2 in symptoms_NS_list:
            if item in symp2:
                Point['신경외과']+=1
                break
        for symp3 in symptoms_OS_list:
            if item in symp3:
                Point['정형외과']+=1
                break
        for symp4 in symptoms_IM_list:
            if item in symp4:
                Point['내과']+=1
                break
        for symp5 in symptoms_DER_list:
            if item in symp5:
                Point['피부과']+=1
                break
        for symp6 in symptoms_ENT_list:
            if item in symp6:
                Point['이비인후과']+=1
                break    
    print(Point)
    max_point_hospital = max(Point,key=Point.get)

def load_hospital_data(mysi,mygu,mydong):
    target_hospital = max_point_hospital
    connection = sqlite3.connect('Hosital_info.db')
    cursor = connection.cursor()
    cursor.execute(f"drop view if exists searchresult")
    cursor.execute(f"create view searchreSult as SELECT hinfo.요양기관명, 진료과목코드명 , 주소,전화번호,과목별전문의수 ,총의사수, x좌표,y좌표 \
           FROM 진료과목정보 as code, 병원정보 as hinfo \
           where 진료과목코드명 = '{target_hospital}' and hinfo.암호화요양기호 = code.암호화요양기호 and 주소 like '%{mygu}%' and 주소 like '%{mydong}%' order by 과목별전문의수 desc")
    connection.commit()
    cursor.execute(f"SELECT * FROM SearchResult")
    myresult = cursor.fetchall()
    
    for attribute in cursor.description:
        print(attribute[0], end=' ')
    print()
    for x in myresult:
        print(x)
    
    want_info = input("원하시는 병원을 입력해주세요  ")
    cursor.execute(f"SELECT x좌표,y좌표 FROM SearchResult where 요양기관명='{want_info}'")
    get_image(cursor.fetchone())

def get_image(coordinate):
    client_id = "0r6b6bcd3x"
    client_secret = "O6Kv2rPejk2y1fDddXoGAcE14d0Wwy2p846Of5bz"
    
    endpoint = "https://naveropenapi.apigw.ntruss.com/map-static/v2/raster"
    headers = {
        "X-NCP-APIGW-API-KEY-ID": client_id,
        "X-NCP-APIGW-API-KEY": client_secret,
    }
    lon, lat = coordinate[0], coordinate[1]
    
    _center = f"{lon},{lat}" # 필수
    _level = 15              # 보기쉽게하기 위한 필수 
    _w, _h = 500, 300        # 필수 이미지 크기

    _format = "png"          # 파일 포맷 / 원본 이미지를 위한 png 포맷 
    _scale = 2               # 고해상도를 위한 설정
    _markers = f"""type:d|size:mid|pos:{lon} {lat}|color:red""" # 위치를 마킹하기 위한 파라미터
    
    _dataversion = ""       # 서비스에서 사용할 데이터 버전 파라미터 전달 CDN 캐시 무효화

    # URL
    url = f"{endpoint}?center={_center}&level={_level}&w={_w}&h={_h}&format={_format}&scale={_scale}&markers={_markers}&dataversion={_dataversion}"
    res = requests.get(url, headers=headers)

    image_data = io.BytesIO(res.content)
    image = Image.open(image_data)
    image.show()
    
    
if __name__== '__main__':
    load_symp_dataset()
    #get_response("목이 쉬었다, 열이 난다, 기침을 한다, 배가 아프다, 몸살이 났다")
    get_response("등이 가렵다, 두드러기가 생겼다, 피부가 건조하다")
    
    analysis_symp()
    load_hospital_data("인천","부평구","삼산동")