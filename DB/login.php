// login.php

<?php
    $con = mysqli_connect("localhost", "root", "admin", "parking_service");
    mysqli_query($con,'SET NAMES utf8');

    $id = $_POST["id"];
    $phone = $_POST["phone"];

    $statement = mysqli_prepare($con, "SELECT * FROM user WHERE id = ? AND phone = ?");
    mysqli_stmt_bind_param($statement, "ss", $id, $phone);
    mysqli_stmt_execute($statement);


    mysqli_stmt_store_result($statement);
    mysqli_stmt_bind_result($statement, $id, $ssn, $name, $phone, $license_plate_number);


    $sql ="SELECT * FROM user WHERE id = '$id'";
    $ret = mysqli_query($con, $sql);
    if($row = mysqli_fetch_array($ret)) {
    }
    else{
        echo "error1";
        exit();
    }
    // $park_id = $row['park_id'];
    $car = $row['license_plate_number'];

    
    $sql ="SELECT * FROM car WHERE license_plate_number = '$car'";
    $ret = mysqli_query($con, $sql);
    if($row = mysqli_fetch_array($ret)) {
    }
    else{
        echo "error2";
        exit();
    }
    $park_id = $row['park_id'];
    $userEntry = $row['entry_time'];
    $discount = $row['discount'];

    $sql ="SELECT * FROM parking_lot WHERE park_id = '$park_id'";
    $ret = mysqli_query($con, $sql);
    if($row = mysqli_fetch_array($ret)) {
    }
    else{
        echo "error3";
        exit();
    }
    $fee = $row['fee_per_10min'];

    date_default_timezone_set('Asia/Seoul');
    $pay_time = date('Y-m-d H:i:s');
    $parking_time = strtotime($pay_time) - strtotime("$userEntry GMT");  // 분 단위
    $d = 24*60*date('d', $parking_time) - 1440;
    $h = 60*date('H', $parking_time);
    $m = date('i', $parking_time);
    $time_diff = $d + $h + $m;    
    $userFee = ($time_diff / 10 - ($time_diff % 10) / 10) * $fee;  // parking_fee: parking_lot -> fee per 10'', car -> 주차시간 => 주차요금

    if($discount == 1)  // 경차
        $userFee = $userFee*0.7;  // 30% 할인
    elseif($discount == 2)  // 전기차
        $userFee = $userFee*0.8;  // 20% 할인

    $response = array();
    $response["success"] = false;
    $response["userEntry"] = $userEntry;
    $response["userFee"] = $userFee;

    while(mysqli_stmt_fetch($statement)) {

        $response["success"] = true;
        $response["userID"] = $id;
        $response["userPhone"] = $phone;
        $response["userName"] = $name;
        $response["userCar"] = $license_plate_number;
        $response["userSsn"] = $ssn;

    }

    echo json_encode($response);



?>