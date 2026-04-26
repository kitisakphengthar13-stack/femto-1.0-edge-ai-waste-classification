import Jetson.GPIO as GPIO
import time
import sys

# Hardware Configuration
SERVO_ROTATE_PIN = 32
SERVO_TILT_PIN = 33

START_ROTATE_DUTY = 7.5
START_TILT_DUTY = 4.12

# Servo Motor Control Module
class Servo:
    """Hardware PWM wrapper for Jetson.GPIO handling state and duty cycle updates."""
    def __init__(self, pin, freq=50):
        self.pin = pin
        self.freq = freq
        self.pwm = None
        self._started = False
        try:
            self.pwm = GPIO.PWM(pin, freq)
        except Exception as e:
            print(f"[ERROR] PWM initialization failed on pin {pin}: {e}")
            self.pwm = None

    def start(self, duty=0.0):
        if self.pwm is None:
            return False
        if self._started:
            try:
                self.pwm.ChangeDutyCycle(float(duty))
                return True
            except Exception:
                return False
        try:
            self.pwm.start(float(duty))
            self._started = True
            return True
        except Exception as e:
            print(f"[ERROR] PWM start failed on pin {self.pin}: {e}")
            self._started = False
            return False

    def set_duty(self, duty):
        if self.pwm is None or not self._started:
            return False
        try:
            self.pwm.ChangeDutyCycle(float(duty))
            return True
        except Exception:
            return False

    def stop(self):
        if self.pwm is None or not self._started:
            return
        try:
            self.pwm.ChangeDutyCycle(0)
            self.pwm.stop()
        except Exception:
            pass
        self._started = False

# Main Calibration Procedure
def main():
    print("[INFO] Starting Servo Calibration Tool")
    
    # Initialize GPIO mode (Assumes hardware pinmux is already configured)
    GPIO.setmode(GPIO.BOARD)

    # Initialize servo instances
    servo_rotate = Servo(SERVO_ROTATE_PIN)
    servo_tilt = Servo(SERVO_TILT_PIN)

    # Move to initial positions
    print(f"[INFO] Initializing default positions -> Pin 32: {START_ROTATE_DUTY}%, Pin 33: {START_TILT_DUTY}%")
    if servo_rotate.start(START_ROTATE_DUTY):
        time.sleep(0.05)
    if servo_tilt.start(START_TILT_DUTY):
        time.sleep(0.05)
    
    # Allow mechanical movement completion before releasing rotation PWM
    time.sleep(1.0)
    servo_rotate.set_duty(0)

    print("\n--- Calibration Menu ---")
    print("Format: [PIN] [DUTY_CYCLE]")
    print("Example: 32 5.0")
    print("Example: 32 0   (Release PWM)")
    print("Command 'q' to exit.")
    print("------------------------\n")

    try:
        while True:
            user_input = input("Command: ").strip().lower()
            
            if user_input == 'q':
                break
                
            parts = user_input.split()
            if len(parts) != 2:
                print("[ERROR] Invalid format. Require: [PIN] [DUTY_CYCLE]")
                continue
                
            pin_str, duty_str = parts
            
            try:
                pin = int(pin_str)
                duty = float(duty_str)
            except ValueError:
                print("[ERROR] Numeric values required.")
                continue

            # Process PWM updates
            if pin == SERVO_ROTATE_PIN:
                if duty == 0:
                    servo_rotate.set_duty(0)
                    print("[SUCCESS] Pin 32 PWM Released")
                else:
                    servo_rotate.set_duty(duty)
                    print(f"[SUCCESS] Pin 32 duty cycle set to {duty}%")
            elif pin == SERVO_TILT_PIN:
                servo_tilt.set_duty(duty)
                print(f"[SUCCESS] Pin 33 duty cycle set to {duty}%")
            else:
                print("[ERROR] Unknown Pin. Supported pins: 32, 33.")

    except KeyboardInterrupt:
        pass
    finally:
        print("\n[INFO] Releasing hardware resources and exiting.")
        servo_rotate.stop()
        servo_tilt.stop()
        GPIO.cleanup()

if __name__ == "__main__":
    main()