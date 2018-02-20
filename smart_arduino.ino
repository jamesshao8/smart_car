

int led = 13;
float duration;                
float distance;              
int srfPin = 8;

void setup() 
{
    Serial.begin(9600);
    pinMode(led, OUTPUT); 
    pinMode(9,OUTPUT);
    pinMode(10,OUTPUT);
    pinMode(5,OUTPUT); 
    pinMode(6,OUTPUT);
    
    
}
void loop()
{
    delay(100);               // wait for a second
    
    if (Serial.available()>0)
    {
      char cmd = Serial.read();
      //Serial.print(cmd);
      switch (cmd)
      {
        case '1':
            Forward();
            break;
        case '2':
            Back();
            break;
        case '3':
            Turn_left();
            break;
        case '4':
            Turn_right();
            break;
        //case '6':
        //    Measure();
        default:
            Stop();
      }
    }
    Measure();
}
void Forward()
{
    digitalWrite(9,HIGH);
    digitalWrite(10,LOW);
    digitalWrite(5,HIGH);
    digitalWrite(6,LOW);
}
void Back()
{
    digitalWrite(9,LOW);
    digitalWrite(10,HIGH);
    digitalWrite(5,LOW);
    digitalWrite(6,HIGH);
}
void Turn_right()
{
    digitalWrite(9,LOW);
    digitalWrite(10,HIGH);
    digitalWrite(5,HIGH);
    digitalWrite(6,LOW);
}
void Turn_left()
{
    digitalWrite(9,HIGH);
    digitalWrite(10,LOW);
    digitalWrite(5,LOW);
    digitalWrite(6,HIGH);
}

void Stop()
{
    digitalWrite(9,LOW);
    digitalWrite(10,LOW);
    digitalWrite(5,LOW);
    digitalWrite(6,LOW);
}

void Measure()
{
      pinMode(srfPin, OUTPUT); 
      digitalWrite(srfPin, LOW);            
      delayMicroseconds(2); 
      digitalWrite(srfPin, HIGH);           
      delayMicroseconds(10); 
      digitalWrite(srfPin, LOW);            
      pinMode(srfPin, INPUT); 
      duration = pulseIn(srfPin, HIGH);         
      distance = duration/58;
      Serial.print(":");       
      Serial.print(distance);
      Serial.println(";");     
      delay(50);  
}

