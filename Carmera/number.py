'''
Mobile Parking Control System
number.py
'''

# 테서랙트를 이용한 number.py
# 모듈화 진행 완료
from unittest import result
import cv2
import Classification as cf
import numpy as np
import matplotlib.image as img 
import matplotlib.pyplot as plt
import pytesseract

# 번호판 출력
MAX_DIAG_MULTIPLYER = 5 # 5
MAX_ANGLE_DIFF = 12.0 # 12.0
MAX_AREA_DIFF = 0.5 # 0.5
MAX_WIDTH_DIFF = 0.8
MAX_HEIGHT_DIFF = 0.2
MIN_N_MATCHED = 3 # 3

#똑바로 돌리기
PLATE_WIDTH_PADDING = 1.3 # 1.3
PLATE_HEIGHT_PADDING = 1.5 # 1.5
MIN_PLATE_RATIO = 3
MAX_PLATE_RATIO = 10
#어떤게 번호판처럼 생겼는지?

MIN_AREA = 80
MIN_WIDTH, MIN_HEIGHT = 2, 10
MIN_RATIO, MAX_RATIO = 0.5, 1.0

def find_chars(contour_list):
    matched_result_idx = []
    
    for d1 in contour_list:
        matched_contours_idx = []
        for d2 in contour_list:
            if d1['idx'] == d2['idx']:
                continue

            dx = abs(d1['cx'] - d2['cx'])
            dy = abs(d1['cy'] - d2['cy'])

            diagonal_length1 = np.sqrt(d1['w'] ** 2 + d1['h'] ** 2)

            distance = np.linalg.norm(np.array([d1['cx'], d1['cy']]) - np.array([d2['cx'], d2['cy']]))
            if dx == 0:
                angle_diff = 90
            else:
                angle_diff = np.degrees(np.arctan(dy / dx))
            area_diff = abs(d1['w'] * d1['h'] - d2['w'] * d2['h']) / (d1['w'] * d1['h'])
            width_diff = abs(d1['w'] - d2['w']) / d1['w']
            height_diff = abs(d1['h'] - d2['h']) / d1['h']

            if distance < diagonal_length1 * MAX_DIAG_MULTIPLYER \
            and angle_diff < MAX_ANGLE_DIFF and area_diff < MAX_AREA_DIFF \
            and width_diff < MAX_WIDTH_DIFF and height_diff < MAX_HEIGHT_DIFF:
                matched_contours_idx.append(d2['idx'])

        # append this contour
        matched_contours_idx.append(d1['idx'])

        if len(matched_contours_idx) < MIN_N_MATCHED:
            continue

        matched_result_idx.append(matched_contours_idx)

        unmatched_contour_idx = []
        for d4 in contour_list:
            if d4['idx'] not in matched_contours_idx:
                unmatched_contour_idx.append(d4['idx'])

        unmatched_contour = np.take(contour_list, unmatched_contour_idx)
        
        # recursive
        recursive_contour_list = find_chars(unmatched_contour)
        
        for idx in recursive_contour_list:
            matched_result_idx.append(idx)

        break

    return matched_result_idx

# 1단계 이미지 전처리
def labeling_bulid_1(img_ori):
    try :
        height, width, channel = img_ori.shape
    except AttributeError :
        return None, None
    possible_contours = []
    '''
    1차 이미지 전처리
    이미지를 흑백조로 전환하고 모폴로지를 통해 차량 이미지에서 부풀리고 줄임으로 노이즈를 1차로 제거
    가우시안 블러링을 통해 이미지의 윤곽선을 매끄럽게 수정함
    '''
    gray = cv2.cvtColor(img_ori, cv2.COLOR_BGR2GRAY)

    structuringElement = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))

    imgTopHat = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, structuringElement)
    imgBlackHat = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, structuringElement)
    
    imgGrayscalePlusTopHat = cv2.add(gray, imgTopHat)
    gray = cv2.subtract(imgGrayscalePlusTopHat, imgBlackHat)
    img_blurred = cv2.GaussianBlur(gray, ksize=(5, 5), sigmaX=0)
    '''
    Edge에 대해 블러링이 된 이미지에 스레시홀드를 가하여 회색조 이미지에서 흑백 반전을 일으킴
    Adaptive Thresholding 기법중 Mean_Thresholding을 채택
    Mean_Threshold는 번호판을 흐리게 하기 보다 이미지를 매끄럽게 처리하여 OCR의 인식율이 좋아짐
    Gaussian_Thresholding 은 반대로 이미지를 더 흐리게 만들어 OCR의 인식율이 낮아짐
    '''
    img_thresh = cv2.adaptiveThreshold(
        img_blurred, 
        maxValue=255.0, 
        adaptiveMethod=cv2.ADAPTIVE_THRESH_MEAN_C, 
        thresholdType=cv2.THRESH_BINARY_INV, 
        blockSize=19, 
        C=9
        )
    contours, _ = cv2.findContours(
        img_thresh, 
        mode=cv2.RETR_LIST, 
        method=cv2.CHAIN_APPROX_SIMPLE
        )
    '''
    컨투어는 컴퓨터가 물체라고 생각하는 모든 범위에 대해 원하는 모양으로 틀을 그려준다.
    관심영역을 검출하기 위해 원본 이미지와 동일한 크기의 검은색 이미지를 생성한다.
    생성된 이미지에 컨투어를 그린다.
    탐지된 컨투어에 의해 그려진 Bounding Box의 넓이를 계산하고 번호의 사이즈 범위를 만족 못하면 posible_contour list에 추가하지 않는다.
    '''
    temp_result = np.zeros((height, width, channel), dtype=np.uint8)
    cv2.drawContours(temp_result, contours=contours, contourIdx=-1, color=(255, 255, 255))
    temp_result = np.zeros((height, width, channel), dtype=np.uint8)
    contours_dict = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        cv2.rectangle(temp_result, pt1=(x, y), pt2=(x+w, y+h), color=(255, 255, 255), thickness=2)
    
    # insert to dict
        contours_dict.append({
            'contour': contour,
            'x': x,
            'y': y,
        'w': w,
        'h': h,
        'cx': x + (w / 2),
        'cy': y + (h / 2)
    })
    # 각 바운딩박스의 크기를 계산하고 스레시홀딩 범위에서 벗어나면 리스트에 넣지 않음
    # 그리고 범위안에 들어온 컨투어는 find_char 함수에서 2차 필터링
    cnt = 0
    for d in contours_dict:
        area = d['w'] * d['h']
        ratio = d['w'] / d['h']
    
        if area > MIN_AREA \
        and d['w'] > MIN_WIDTH and d['h'] > MIN_HEIGHT \
        and MIN_RATIO < ratio < MAX_RATIO:
            d['idx'] = cnt
            cnt += 1
            possible_contours.append(d)
    temp_result = np.zeros((height, width, channel), dtype=np.uint8)
    # 번호판의 번호 범위에 든 바운딩박스에 대해 전처리된 이미지에 적용시킨다.
    for d in possible_contours:
        cv2.rectangle(temp_result, pt1=(d['x'], d['y']), pt2=(d['x']+d['w'], d['y']+d['h']), color=(255, 255, 255), thickness=2)
    try :
        result_idx = find_chars(possible_contours)
    # IndexError 예외처리
    except IndexError :
        return None, None
    matched_result = []
    for idx_list in result_idx:
        matched_result.append(np.take(possible_contours, idx_list))

    '''
    새로 검은색 배경의 이미지를 생성한다. 이는 번호라고 가정한 바운딩박스만을 새로 그리기 위함
    최종적으로 번호라고 레이블링 된 컨투어에 대해 rectangle 함수로 박스를 그리고 이 박스들의 너비와 높이를 구하여
    번호판의 넓이를 계산하고 info라는 리스트에 각 꼭짓점을 저장한다.
    '''
    temp_result = np.zeros((height, width, channel), dtype=np.uint8)
    for r in matched_result:
        for d in r:
#         cv2.drawContours(temp_result, d['contour'], -1, (255, 255, 255))
            cv2.rectangle(temp_result, pt1=(d['x'], d['y']), pt2=(d['x']+d['w'], d['y']+d['h']), color=(255, 255, 255), thickness=2)
    plate_imgs = []
    plate_infos = []
    for i, matched_chars in enumerate(matched_result):
        sorted_chars = sorted(matched_chars, key=lambda x: x['cx'])
        plate_cx = (sorted_chars[0]['cx'] + sorted_chars[-1]['cx']) / 2
        plate_cy = (sorted_chars[0]['cy'] + sorted_chars[-1]['cy']) / 2
    
        plate_width = (sorted_chars[-1]['x'] + sorted_chars[-1]['w'] - sorted_chars[0]['x']) * PLATE_WIDTH_PADDING
        sum_height = 0
        for d in sorted_chars:
            sum_height += d['h']

        plate_height = int(sum_height / len(sorted_chars) * PLATE_HEIGHT_PADDING)
        triangle_height = sorted_chars[-1]['cy'] - sorted_chars[0]['cy']
        triangle_hypotenus = np.linalg.norm(
        np.array([sorted_chars[0]['cx'], sorted_chars[0]['cy']]) - 
        np.array([sorted_chars[-1]['cx'], sorted_chars[-1]['cy']])
    )
        '''
        해당 라인에서 연속적으로 이미지 프로세싱을 시도 할 시 오류가 있었음
        첫번째에서는 반환되는 list의 개수가 1개 이나, 2번째 부터는 2개 이상을 반환
        보정을 위해 컨볼루션을 거치는 것으로 보임, 마지막 리스트 내의 numpy array가 보정된 번호판 위치 특성인데 이전에 연산된 특징들 까지 중복으로 적용되었음
        이는 각 픽셀값의 변환행렬이 이전의 이미지의 데이터가 그대로 리스트에 저장되어 img_rotated, 회전된 이미지 데이터가 다른 데이터와 같은 리스트에 저장되는 현상
        가장 최근의 이미지 데이터 행렬을 추출하고 이를 반환하여 해결
        프로세스된 특징을 추출하고 리스트화 하여 번호판의 위치 특성을 labeling_bulid_1 함수에서 반환함
        Parameta
        angle : 이미지에 대해 얼마나 회전해야 하는지, 즉 수평이 되기 위해 얼마나 각도를 돌려야하는지 계산
        rotation_matrix : getRotationMatrix2D는 Rotate 연산시 이미지의 중앙점을 기준으로 회전, 2*3 Affine Matrix, 변환행렬을 반환
        img_rotated : rotation_matrix 변환행렬을 이용하여 번호판을 가지런하게 돌린다.
        
        '''
        # 이미지의 각도를 계산
        angle = np.degrees(np.arcsin(triangle_height / triangle_hypotenus))
        # 이미지에 대해 Rotation, 중앙점을 기준으로
        rotation_matrix = cv2.getRotationMatrix2D(center=(plate_cx, plate_cy), angle=angle, scale=1.0)
        # 회전적용
        img_rotated = cv2.warpAffine(img_thresh, M=rotation_matrix, dsize=(width, height)) 
        # 적용한 이미지에 대해 이전에 컨투어 영역을 활용하여 번호판 영역 적용  
        img_cropped = cv2.getRectSubPix(
        img_rotated, 
        patchSize=(int(plate_width), int(plate_height)), 
        center=(int(plate_cx), int(plate_cy))
    ) 
        if img_cropped.shape[1] / img_cropped.shape[0] < MIN_PLATE_RATIO or img_cropped.shape[1] / img_cropped.shape[0] < MIN_PLATE_RATIO > MAX_PLATE_RATIO:
            continue
    
        plate_imgs.append(img_cropped)
        plate_infos.append({
        'x': int(plate_cx - plate_width / 2),
        'y': int(plate_cy - plate_height / 2),
        'w': int(plate_width),
        'h': int(plate_height)
    })
    # 차량 이미지가 잘못되어 컨투어 생성에 실패한 경우 Error를 출력하고 None을 반환한다.
    if plate_imgs == None :
        print("Error")
        return None, None
    # plate_imgs는 번호판 위치를 보정 후 번호판의 왜곡되지 않은 특성을 numpy.array 형태로 가지게 됨
    # 만약 보정이 따로 들어가지 않았다면 해당 조건을 실행
    if len(plate_imgs) == 1 :
        np.squeeze(plate_imgs)
        # labeling_bulid_2 함수에서는 전처리 이미지와 번호판의 4개의 꼭짓점을 저장한 리스트를 반환한다.
        return plate_imgs, plate_infos
    # 보정이 들어갔다면 해당 조건을 실행
    # 가장 최근에 들어온 이미지 데이터를 추출하고 리스트로 매핑하여 반환
    else :
        try :
            np.squeeze(plate_imgs)
            new_plate = plate_imgs.pop()
            new_plate = [new_plate]
        except IndexError :
            return None, None
        # labeling_bulid_2 함수에서는 전처리 이미지와 번호판의 4개의 꼭짓점을 저장한 리스트를 반환한다.
        return new_plate, plate_infos
def labeling_bulid_2(MIN_AREA, MIN_WIDTH, MIN_HEIGHT, MIN_RATIO, MAX_RATIO, plate_imgs,plate_infos, ori_img):
    '''
    labeling_bulid_2 함수는 번호판 이미지 객체와 원본이미지, 그리고 labeling_1 함수에서 탐지한 번호판 좌표(리스트)를 받아온다.
    검출된 번호판은 2차적으로 전처리를 하고 각 바운딩박스에서 추출된 2차원 특징 벡터를 테서랙트 OCR과 대조한다.
    동작 방식은 MNIST의 문자 판독과 비슷한 대조 방식
    OCR에서 라벨링되어 반환된 string 문자열은 main.py 에서 최종적으로 예외처리를 거친 후 성공/실패 여부를 판단한다.
    '''
    longest_idx, longest_text = -1, 0
    plate_chars = []
    # 번호판 사이즈를 보정
    for i, plate_img in enumerate(plate_imgs):
        plate_img = cv2.resize(plate_img, dsize=(0, 0), fx=1.6, fy=1.6)
        _, plate_img = cv2.threshold(plate_img, thresh=0.0, maxval=255.0, type=cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(plate_img, mode=cv2.RETR_LIST, method=cv2.CHAIN_APPROX_SIMPLE)
    
        plate_min_x, plate_min_y = plate_img.shape[1], plate_img.shape[0]
        plate_max_x, plate_max_y = 0, 0
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
        
            area = w * h
            ratio = w / h
            
            if area > MIN_AREA \
        and w > MIN_WIDTH and h > MIN_HEIGHT \
        and MIN_RATIO < ratio < MAX_RATIO:
                if x < plate_min_x:
                    plate_min_x = x
                if y < plate_min_y:
                    plate_min_y = y
                if x + w > plate_max_x:
                    plate_max_x = x + w
                if y + h > plate_max_y:
                    plate_max_y = y + h
        '''
        카메라를 이용하여 직접 차량을 촬영 시 최적의 표준편차는 0.3
        차량을 촬영하는게 아닌 기존의 사진을 이용하여 입력 시 최적의 표준편차는 0.4~0.5 사이
        커널은 3,3 이 적당함, 표준편차를 높임으로 강한 성분에 대해 무디게, 잡성분에 대해서도 약한 스무딩을 주어 OCR에서의 판독율을 향상시킴
        '''
        img_result = plate_img[plate_min_y:plate_max_y+5, plate_min_x:plate_max_x+10]
        try :
            # 전처리된 이미지에서 검출된 번호판에 대해 가우시안 블러링을 하여 번호판에서의 잡음을 제거
            # 표준편차를 주는 이유는 검출된 영역이 크지 않기 때문에 스무딩을 강하게 가할 시 문자가 있는 픽셀부분까지 흐려지므로 분포를 완만하게 함
            img_result = cv2.GaussianBlur(img_result, ksize=(3, 3), sigmaX=0.3)
        except IndexError :
            return None, None
        # 검은색인 차량 번호 외에 모든 밝기성분에 대해 스레시홀딩하여 차량 번호외에 모든 픽셀을 반전시킨다.
        _, img_result = cv2.threshold(img_result, thresh=0.0, maxval=255.0, type=cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        # 라벨링된 번호판을 matplotlib를 이용하여 시각화
        plt.imshow(img_result)
        plt.show()
        # OCR을 불러오고 imge_to_string 함수를 이용하여 전처리된 번호판에 있는 문자를 검출
        pytesseract.pytesseract.tesseract_cmd = 'C:\\Users\\LUA\\Documents\\Tesseract-OCR\\tesseract.exe'
        chars = pytesseract.image_to_string(img_result, lang='kor', config='--psm 7 --oem 0')
        result_chars = ''
        has_digit = False
        # 판독된 문자열에서 필터링
        for c in chars:
            if ord('가') <= ord(c) <= ord('힣') or c.isdigit():
                if c.isdigit() :
                    has_digit = True
                result_chars += c
        if has_digit and len(plate_chars) > longest_text:
            longest_idx = i
        # labeling_bulid_1 함수에서 계산된 번호판 4개의 꼭짓점 리스트를 이용하여 copy한 원본 이미지에서 번호판을 잘라내고 번호판을 구분해냄
        # 리스트에는 x_max, x_min, y_max, y_min 사각형의 각 꼭짓점 좌표값이 저장됨
        info = plate_infos[longest_idx]
        # 경차 모델에 원본 이미지를 적용
        isDiscount = cf.isCompactCar(ori_img)
        # 만약 경차가 아니라면 전기차 판별 함수로 이동
        if isDiscount != 1 :        
            isDiscount = cf.isElectric(info, ori_img)
        # 최종적으로 라벨링된 번호 검사
        # 문자열의 크기가 7,8이 아니라면 잘못 인식된 경우로 None 으로 리턴, 이는 main에서 None으로 받을 시 재 촬영을 시도
        if len(result_chars) >= 7 or len(result_chars) <= 9 :
            return result_chars, isDiscount
        else :
            return None, None