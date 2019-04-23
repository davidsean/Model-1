#ifdef INCLUDE_ROCKER 

# define ROCKER_MAX_ANGLE 20 // max angle on both +/- directions
# define ROCKER_SPEED 10  // (nominal) speed, degrees of ratation per sec

class IncuversRockingingSystem {
  private:
    int pinAssignment;
    Servo rocker_servo; 
    boolean enabled;
    boolean currentlyOn;
    boolean reverse;
    long prevTime;
    long tickTime;

    int last_target;
   
  public:
    void SetupRocker(int pin, boolean enabled) {
      #ifdef DEBUG_ROCKER
        Serial.println(F("Rocker::Setup"));
        Serial.println(pin);
        Serial.println(enabled);
      #endif
      
      // Setup
       this->pinAssignment = pin;
       this->enabled = enabled;
       this->reverse = 0;
       this->last_target = 0;
       this->prevTime = millis();
       this->rocker_servo.attach(this->pinAssignment);
    }

    void MakeSafeState() {
      #ifdef DEBUG_ROCKER
        Serial.println(F("ROCKER::SafeState"));
      #endif
    }
    void DoTick() {
      long tickTime = millis();
      //time since last call
      long deltaTime = tickTime - this->prevTime; 
      int current_pos = this ->rocker_servo.read();
      int targetPos = current_pos + ROCKER_SPEED*(1-this->reverse*2);

      #ifdef DEBUG_ROCKER
        Serial.println(F("Rocker::Debug"));
        Serial.println(current_pos);
        //Serial.println(targetPos);
      #endif

      
      if (((90+ROCKER_MAX_ANGLE)>targetPos) && (!reverse)) { // forward, far from end
        #ifdef DEBUG_ROCKER
          //Serial.println(F("Rocker::Debug: forward, far from end"));
          //Serial.println((90+ROCKER_MAX_ANGLE));
        #endif
          this->rocker_servo.write(targetPos);
          this->prevTime = tickTime;
          return;
      }
      if (((90+ROCKER_MAX_ANGLE)<=targetPos) && (!reverse)) { // forward, close to end 
        #ifdef DEBUG_ROCKER
          //Serial.println(F("Rocker::Debug: forward, close to end"));
          //Serial.println((90+ROCKER_MAX_ANGLE));
        #endif

          this->rocker_servo.write(ROCKER_MAX_ANGLE+90); 
          this->prevTime = tickTime;
          this->reverse = 1; //go backward
          return;
      }
      if (((90-ROCKER_MAX_ANGLE)>=targetPos) && (reverse)) { // backward, close to end
        #ifdef DEBUG_ROCKER
          //Serial.println(F("Rocker::Debug: backward, close to end"));
          //Serial.println((90-ROCKER_MAX_ANGLE));
        #endif

          this->rocker_servo.write((90-ROCKER_MAX_ANGLE));
          this->prevTime = tickTime;
          this->reverse = 0; //go forward
          return;
      }
      if (((90-ROCKER_MAX_ANGLE)<targetPos) && (reverse)) { // backward, far from end
        #ifdef DEBUG_ROCKER
          //Serial.println(F("Rocker::Debug: backward, far from end"));
          //Serial.println((90-ROCKER_MAX_ANGLE));
        #endif

          this->rocker_servo.write(targetPos);
          this->prevTime = tickTime;
          return;
      }

    }
    char GetSerialAPIndicator() {
      return GetIndicator(this->currentlyOn, false, false, true);
    }

    char GetNewUIIndicator() {
      return GetIndicator(this->currentlyOn, false, false, true);
    }

    
};
#else
class IncuversRockingSystem {
  private:
  public:
    void SetupRocker(int pin, boolean enabled) {
    }

    void MakeSafeState() {
    }
  
    void DoTick() {
    }

    void UpdateMode(int mode) {
    }

    char GetSerialAPIndicator() {
      return 'x';
    }

    String GetOldUIDisplay() {
      return F("LED: not incl.");
    }

    char GetNewUIIndicator() {
      return 'x';
    }

    String GetNewUIReading() {
      return F("n/i");
    }
};
#endif
