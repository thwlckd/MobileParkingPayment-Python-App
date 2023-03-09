package com.example.parking_app;

import androidx.appcompat.app.AppCompatActivity;

import com.android.volley.AuthFailureError;
import com.android.volley.Response;
import com.android.volley.toolbox.StringRequest;

import java.util.HashMap;
import java.util.Map;

public class RegisterRequest extends StringRequest {

    // 서버 URL 설정 ( PHP 파일 연동 )
    final static private String URL = "http://165.229.125.154/register.php";
    private Map<String, String> map;


    public RegisterRequest(String userID, String userCar, String userName, String userSsn, String userPhone, Response.Listener<String> listener) {
        super(Method.POST, URL, listener, null);

        map = new HashMap<>();
        map.put("userID",userID);
        map.put("userCar", userCar);
        map.put("userName", userName);
        map.put("userSsn", userSsn);
        map.put("userPhone", userPhone);

        // map.put("userAge", userAge + "");
    }

    @Override
    protected Map<String, String> getParams() throws AuthFailureError {
        return map;
    }
}
