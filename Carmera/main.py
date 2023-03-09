'''
Mobile Parking Control System
main.py
'''
import tensorflow_hub as hub
import cv2
import pandas as pd
import Classification as Cf
from number import labeling_bulid_1
from number import labeling_bulid_2
import DB as db
import tensorflow
import os 
os.environ['TFHUB_CACHE_DIR'] = '/home/user/workspace/tf_cache'
detects = hub.load("https://tfhub.dev/tensorflow/efficientdet/lite2/detection/1")
labels = pd.read_csv('labels.csv',sep=';',index_col='ID')
# labels.csv 파일에서 label을 numpyArray 화 하여 배열로 저장합니다
labels = labels['OBJECT (2022 REL.)']
scale = 30
location = 1
MIN_AREA = 80
MIN_WIDTH, MIN_HEIGHT = 2, 8
MIN_RATIO, MAX_RATIO = 0.25, 1.0
conn = db.con_and_make_cursor()
cursor = conn.cursor()
select = "SELECT * FROM administrator AS admin, parking_lot as PL WHERE admin.management_park = %s = PL.park_id = %s"
cursor.execute(select, (location, location))
result = cursor.fetchall()
print("관리자 명 :", result[0][2],"연락처 :", result[0][3], "10분당 주차 비용(원) :",result[0][9], "지역 :", result[0][7], "현재 주차장 정보 : ",result[0][6], "최대 주차 면적 :", result[0][8])
max_parking_area = result[0][8]
cap = cv2.VideoCapture(0)
counts = 0
while(True) :
        ret, frame = cap.read()
        # 줌인을 하는 함수가 아님, frame/1sec 단위로 모든 프레임을 자른다
        cv2.flip(frame, 1)
        '''
        # 현재 반영되고 있는 프레임의 가로, 세로, 컬러채널 크기를 받아온다
        height, width, channels = frame.shape
        # 중심점 탐색
        centerX,centerY=int(height/2),int(width/2)
        # radius 계산
        radiusX,radiusY= int(scale*height/100),int(scale*width/100)
        # 적용할 새로운 프레임 크기 계산
        minX,maxX=centerX-radiusX,centerX+radiusX
        minY,maxY=centerY-radiusY,centerY+radiusY
        # 프레임 크롭 및 적용
        cropped = frame[minX:maxX, minY:maxY]
        '''
        # 이건 보기 편하게 하기 위해 윈도우 사이즈 확대
        frame_img = cv2.resize(frame, (1024, 640)) 
        # 좌우 반전 시키기
        rgb = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    #Is optional but i recommend (float convertion and convert img to tensor image)
        rgb_tensor = tensorflow.convert_to_tensor(frame_img, dtype=tensorflow.uint8)

    #Add dims to rgb_tensor
        rgb_tensor = tensorflow.expand_dims(rgb_tensor , 0)
    
        boxes, scores, classes, num_detections = detects(rgb_tensor)
    
        pred_labels = classes.numpy().astype('int')[0]
        pred_labels = [labels[i] for i in pred_labels]
        pred_boxes = boxes.numpy()[0].astype('int')
        pred_scores = scores.numpy()[0]
        # object Detection 
        # 디텍터가 돌때 프레임 다운되는 현상 해결
        # for start
        for score, (ymin,xmin,ymax,xmax), label in zip(pred_scores, pred_boxes, pred_labels):
            conn.commit()
            if score < 0.6 or label != 'car' :
            # 시연때는 사진 같은거로 보여줘야 하므로 로스를 높임
                '''
                1.
                학습된 객체 이미지 데이터와 실제 탐지된 객체의 유사도가 70% 미만 인 경우
                더미 바운딩 박스를 생성하여 프레임이 드랍되는 현상을 방지함
                '''
                img_boxes = cv2.rectangle(frame_img,(0, 0),(0, 0),(0,0,0),1)
            else :
                score_txt = f'{100 * round(score,0)}'
                img_boxes = cv2.rectangle(frame_img,(xmin, ymax),(xmax, ymin),(0,0,0),1)   
                font = cv2.FONT_HERSHEY_SIMPLEX
                '''
                2.
                바운딩 박스의 기준이 되는 xmax, xmin, ymax, ymin 의 값을 이용하여 탐지된 객체의 박스 넓이를 계산
                약 계산된 사이즈가 190000이 될때 번호판 인식율이 좋음.
                박스의 크기가 기준에 충족하지 못하면 자동차 객체라도 다음 과정으로 넘어가지 않음
                '''
                x, y = xmax-xmin, ymax-ymin
                size = x * y
                cv2.putText(img_boxes,str(size),(xmin, ymin), font, 0.5, (0,0,0), 1, cv2.LINE_AA)
                result_ck = None
                if label == "car" :
                    # 박스 차량 박스 사이즈가 190000 안된다면 간격이 멀리 있음
                    if size < 190000 :
                        continue
                    else :
                        # 시작
                        print("차량이 감지되었습니다.")
                        print("차량 배경 분리 작업을 시작합니다.")
                    # 크롭된 이미지를 저장하고 파일명을 반환하는 함수 
                        img_name = Cf.Crop_and_save(xmin, xmax, ymin, ymax, img_boxes)
                        print("차량 배경 분리 완료 파일 명 :", img_name)
                        print("차량 번호 라벨링 시도")
                        # car_img는 crop된 이미지 객체에서 받아옵니다.
                        car_img = cv2.imread("Capture/"+ img_name + ".png")
                        # 차량 이미지 전처리 시작
                        plate_img,plate_infos = labeling_bulid_1(car_img)
                        if plate_img == None :
                            continue
                        # 라벨링이 끝난 번호를 반환합니다
                        result_char, isDiscount = labeling_bulid_2(MIN_AREA, MIN_WIDTH, MIN_HEIGHT, MIN_RATIO, MAX_RATIO, plate_img, plate_infos, car_img)
                        if result_char == None  :
                            count = count + 1
                            print("[에러] : 차량 라벨링 실패 현재 ", count, "회 실패!")
                            # 번호판 인식이 잘못되었으므로 해당 이미지는 삭제합니다.
                            try: 
                                os.remove("Capture/" + img_name + ".png")
                            except: pass
                            # 실패 횟수 카운팅을 하여 연달아 실패 시 잠시 대기 후 다시 라벨링을 시도함
                            if count == 3 :
                            # 운전자에게 인식이 실패했다고 알린다.
                                Open = cv2.imread("Failed.png")
                                cv2.imshow("Fail", Open)
                                cv2.waitKey(3000)
                                count = 0
                                continue
                            continue
                        # 제일 앞 글자가 숫자가 아니라면 제일 앞 문자를 지운다.
                        # 보정
                        if result_char[0] < '0' or result_char[0] > '9' :
                            for i in range(1, 8) :
                                try :
                                    correction_char += result_char[i]
                                except IndexError :
                                    print("번호판 정보가 잘못됨.")
                                    result_char = None
                                    continue
                                except TypeError :
                                    print("번호판 정보가 잘못됨.")
                                    result_char = None
                                    continue
                            result_char = None
                            result_char = correction_char
                        # 차량 앞번호가 2자리 인 경우 뒤에 4자리 외에 컷
                        # 보정
                        if result_char[2] < '0' or result_char[2] > '9' :
                            for i in range(0, 7) :
                                try :
                                    correction_char += result_char[i]
                                except IndexError :
                                    print("번호판 정보가 잘못됨.")
                                    result_char = None
                                    continue
                            result_char = None
                            result_char = correction_char
                        # 차량 앞번호가 3자리 인 경우 뒤에 4자리 외에 컷
                        # 보정
                        if result_char[3] < '0' or result_char[3] > '9' :
                            for i in range(0, 8) :
                                try :
                                    correction_char += result_char[i]
                                except IndexError :
                                    print("번호판 정보가 잘못됨.")
                                    result_char = None
                                    continue
                                result_char = None
                                result_char = correction_char
                        if result_char == None :
                            print("라벨링 실패 재시도")
                            continue
                        Check = "SELECT * FROM car WHERE license_plate_number = %s"
                        cursor.execute(Check, (result_char)) 
                        result_ck = cursor.fetchall()
                        if not result_ck :
                            # 데베에 없으면 차 번호 인식 X
                            print("데이터 베이스에 존재 하지 않는 번호입니다. 재인식을 시도합니다.")
                            continue
                        if result_ck[0][1] == None:
                            result_char = Cf.entrance_car(result_char, location, isDiscount)
                            max_parking_area = max_parking_area - 1
                            print("차량 번호 : ", result_char)
                            print("현재 남은 공간 : ", max_parking_area)
                            # 운전자에게 차단기가 열렸다는 신호를 준다
                            Open = cv2.imread("Opened.png")
                            cv2.imshow("Open", Open)
                            cv2.waitKey(3000)
                            cv2.destroyAllWindows()
                            continue
                    # 출차 모드 일시 출차 프로세스 실행
                        else :
                            isPay = Cf.exit_car(result_char, location)
                            if isPay == 0 :
                                Open = cv2.imread("Not.png")
                                cv2.imshow("NotPayment", Open)
                                cv2.waitKey(3000)
                                cv2.destroyAllWindows()
                                continue
                            elif isPay == 1 :
                                max_parking_area = max_parking_area + 1
                            # 운전자에게 차단기가 열렸다는 신호를 준다
                                Open = cv2.imread("Opened.png")
                                cv2.imshow("Open", Open)
                                cv2.waitKey(3000)
                                cv2.destroyAllWindows()
                                continue
        # for end
        cam_name = "screen"
            # 웹캠 오픈
        cv2.imshow(cam_name, img_boxes)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
cap.release()
cv2.destroyAllWindows()