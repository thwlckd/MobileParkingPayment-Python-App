package com.example.parking_app;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ImageButton;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

import com.android.volley.RequestQueue;
import com.android.volley.Response;
import com.android.volley.toolbox.Volley;

import org.json.JSONException;
import org.json.JSONObject;

public class PayActivity extends AppCompatActivity{
    private ImageButton btn_pay;
    private TextView tv_car;


    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_pay);

        tv_car = findViewById(R.id.tv_car);

        Intent intent = getIntent();
        String userCar = intent.getStringExtra("userCar");

        tv_car.setText(userCar);

        btn_pay = findViewById(R.id.btn_pay);
        btn_pay.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                // EditText에 현재 입력되어있는 값을 get(가져온다)해온다.
//                String userID = et_id.getText().toString();
//                String userPhone = et_phone.getText().toString();
//                String userName = et_name.getText().toString();
//                String userCar = et_car.getText().toString();
//                String userSsn = et_ssn.getText().toString();

                // int userAge = Integer.parseInt(et_age.getText().toString());

                Response.Listener<String> responseListener = new Response.Listener<String>() {
                    @Override
                    public void onResponse(String response) {
                        try {
                            JSONObject jsonObject = new JSONObject(response);
                            boolean success = jsonObject.getBoolean("success");
                            if (success) { // 회원등록에 성공한 경우
                                Toast.makeText(getApplicationContext(),"회원 등록에 성공하였습니다.",Toast.LENGTH_SHORT).show();
                                Intent intent = new Intent(PayActivity.this, MainActivity.class);
                                startActivity(intent);
                            } else { // 회원등록에 실패한 경우
                                Toast.makeText(getApplicationContext(),"회원 등록에 실패하였습니다.",Toast.LENGTH_SHORT).show();
                                return;
                            }
                        } catch (JSONException e) {
                            e.printStackTrace();
                        }

                    }
                };
                // 서버로 Volley를 이용해서 요청을 함.
                PayRequest payRequest = new PayRequest(userCar,responseListener);
                RequestQueue queue = Volley.newRequestQueue(PayActivity.this);
                queue.add(payRequest);

            }
        });




    }
}

