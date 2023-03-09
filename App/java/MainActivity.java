package com.example.parking_app;

import androidx.appcompat.app.AppCompatActivity;

import android.content.Intent;
import android.view.View;
import android.widget.Button;
import android.widget.ImageButton;
import android.widget.TextView;

import android.os.Bundle;
import android.widget.Toast;

import com.android.volley.RequestQueue;
import com.android.volley.Response;
import com.android.volley.toolbox.Volley;

import org.json.JSONException;
import org.json.JSONObject;

public class MainActivity extends AppCompatActivity {

    private TextView tv_name, tv_car, tv_entry, tv_fee;
    private ImageButton btn_pay;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        tv_name = findViewById(R.id.tv_name);
        tv_car = findViewById(R.id.tv_car);
        tv_entry = findViewById(R.id.tv_entry);
        tv_fee = findViewById(R.id.tv_fee);
        btn_pay = findViewById(R.id.btn_pay);

        Intent intent = getIntent();
        String userName = intent.getStringExtra("userName");
        String userCar = intent.getStringExtra("userCar");
        String userEntry = intent.getStringExtra("userEntry");
        String userFee = intent.getStringExtra("userFee");

        tv_name.setText(userName);
        tv_car.setText(userCar);
        tv_entry.setText(userEntry);
        tv_fee.setText(userFee);


        // 결제 버튼을 클릭 시 수행
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

                Response.Listener<String> responseListener = new Response.Listener<String>() {
                    @Override
                    public void onResponse(String response) {
                        try {
                            JSONObject jsonObject = new JSONObject(response);
                            boolean success = jsonObject.getBoolean("success");
                            if (success) {
                                Toast.makeText(getApplicationContext(),"결제 성공",Toast.LENGTH_SHORT).show();
                                Intent intent = new Intent(MainActivity.this, LoginActivity.class);
                                startActivity(intent);
                            } else {
                                Toast.makeText(getApplicationContext(),"결제 실패",Toast.LENGTH_SHORT).show();
                                return;
                            }
                        } catch (JSONException e) {
                            e.printStackTrace();
                        }

                    }
                };
                // 서버로 Volley를 이용해서 요청을 함.
                PayRequest payRequest = new PayRequest(userCar, responseListener);
                RequestQueue queue = Volley.newRequestQueue(MainActivity.this);
                queue.add(payRequest);

            }
        });


    }
}