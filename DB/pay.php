<?php
    $con = mysqli_connect("localhost", "root", "admin", "parking_service");
    mysqli_query($con,'SET NAMES utf8');

    // $userID = $_POST["userID"];
    // $userPhone = $_POST["userPhone"];
    $userCar = $_POST["userCar"];
    // $userSsn = $_POST["userSsn"];
    // $userName = $_POST["userName"];

    // $userCar = '265더8065';

    $sql ="SELECT * FROM car WHERE license_plate_number = '$userCar'";
    $ret = mysqli_query($con, $sql);
    if($row = mysqli_fetch_array($ret)) {
    }
    else{
        echo "error1";
        exit();
    }
    $park_id = $row['park_id'];
    $entry_time = $row['entry_time'];
    $discount = $row['discount'];


    $sql ="SELECT * FROM parking_lot WHERE park_id = '$park_id'";
    $ret = mysqli_query($con, $sql);
    if($row = mysqli_fetch_array($ret)) {
    }
    else{
        echo "error2";
        exit();
    }
    $fee = $row['fee_per_10min'];

    $sql ="SELECT * FROM payment";
    $ret = mysqli_query($con, $sql);
    if($row = mysqli_fetch_array($ret)) {
    }
    else{
        echo "error3";
        exit();
    }
    $num = mysqli_num_rows($ret) + 1;

    $sql ="SELECT * FROM user WHERE license_plate_number = '$userCar'";
    $ret = mysqli_query($con, $sql);
    if($row = mysqli_fetch_array($ret)) {
    }
    else{
        echo "error4";
        exit();
    }
    $user_id = $row['id'];

    date_default_timezone_set('Asia/Seoul');

    $pay_num = $num;  // num(rows) + 1 하자
    $pay_time = date('Y-m-d H:i:s');
    $parking_time = strtotime($pay_time) - strtotime("$entry_time GMT");  // 분 단위
    $d = 24*60*date('d', $parking_time) - 1440;
    $h = 60*date('H', $parking_time);
    $m = date('i', $parking_time);
    $time_diff = $d +$h + $m;    
    $park_fee = ($time_diff / 10 - ($time_diff % 10) / 10) * $fee;  // parking_fee: parking_lot -> fee per 10'', car -> 주차시간 => 주차요금

    if($discount == 1)  // 경차
        $park_fee = $park_fee*0.7;  // 30% 할인
    elseif($discount == 2)  // 전기차
        $park_fee = $park_fee*0.8;  // 20% 할인

    $sql = "INSERT INTO payment VALUES ('$pay_num','$pay_time','$park_fee','$user_id')";
    $ret = mysqli_query($con, $sql);
    if($ret){
    }
    else{
        echo "error5";  
        echo mysqli_error($con);
    }


    $sql = "UPDATE car SET pre_order = '1' WHERE license_plate_number = '$userCar'";
    $ret = mysqli_query($con, $sql);
    if($ret){
    }
    else{
        echo "error6";  
        echo mysqli_error($con);
    }



    // $sql_h = "UPDATE parking_lot SET size = size - 1 WHERE park_id = '$park_id'";
    //   $ret_h = mysqli_query($con, $sql_h);
    //   if($ret_h){
    //   }
    //   else{
    //      echo mysqli_error($con);
    //   }


    // $statement = mysqli_prepare($con, "INSERT INTO payment VALUES (?,?,?,?)");
    // mysqli_stmt_bind_param($statement, "ssss", $pay_num, $pay_time, $park_fee, $user_id);
    // mysqli_stmt_execute($statement);

    $response = array();
    $response["success"] = true;

    echo json_encode($response);

?>