// register.php

<?php
    $con = mysqli_connect("localhost", "root", "admin", "parking_service");
    mysqli_query($con,'SET NAMES utf8');

    $userID = $_POST["userID"];
    $userPhone = $_POST["userPhone"];
    $userCar = $_POST["userCar"];
    $userSsn = $_POST["userSsn"];
    $userName = $_POST["userName"];

    $sql = "INSERT INTO car VALUES ('$userCar', NULL, NULL, NULL, 0)";
    $ret = mysqli_query($con, $sql);
    if($ret){
    }
    else{
        echo "error1";  
        echo mysqli_error($con);
    }


    $statement = mysqli_prepare($con, "INSERT INTO user VALUES (?,?,?,?,?)");
    mysqli_stmt_bind_param($statement, "sssss", $userID, $userSsn, $userName, $userPhone, $userCar);
    mysqli_stmt_execute($statement);


    $response = array();
    $response["success"] = true;


    echo json_encode($response);

?>