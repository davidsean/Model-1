#ifdef INCLUDE_PILINK 
/*
 * Incuvers PiLink code.
 * 
 * Only functional on 1.0.0+ control board units.
 * Requires the CRC32 library by Christopher Baker.
 */

#include <CRC32.h>

class IncuversPiLink {
  private:
    IncuversSettingsHandler* incSet;
    bool isEnabled;

    void CheckForCommands() {
      
    }
    
    void SendStatus() {
      // Create string to send
      String piLink = String("");
      //piLink = String(pilink + F(" MS "));                //Time in s
      //piLink = String(piLink + String(millis(), DEC));
      //piLink = String(piLink + F(" ID "));              // Identification
      //piLink = String(piLink + String(incSet->getSerial()));

      //piLink = String(piLink + F(" IV "));              // Ident Version
      //piLink = String(piLink + F(SOFTWARE_VER_STRING));
      // Heating/Fan system
      piLink = String(piLink + F(" FM "));              // Fan, mode
      piLink = String(piLink + String(incSet->getFanMode(), DEC));
      piLink = String(piLink + F(" TM "));              // Temperature, mode
      piLink = String(piLink + String(incSet->getHeatMode(), DEC));
      piLink = String(piLink + F(" TP "));              // Temperature, setpoint
      piLink = String(piLink + String(incSet->getTemperatureSetPoint(), 2));
      piLink = String(piLink + F(" TC "));              // Temperature, chamber
      piLink = String(piLink + String(incSet->getChamberTemperature(), 2));
      piLink = String(piLink + F(" TD "));              // Temperature, door
      piLink = String(piLink + String(incSet->getDoorTemperature(), 2));
      piLink = String(piLink + F(" TO "));              // Temperature, other
      piLink = String(piLink + String(incSet->getOtherTemperature(), 2));
      piLink = String(piLink + F(" TS "));              // Temperature, status
      piLink = String(piLink + String(GetIndicator(incSet->isDoorOn(), incSet->isDoorStepping(), false, true)));
      piLink = String(piLink + String(GetIndicator(incSet->isChamberOn(), incSet->isChamberStepping(), false, true)));
      piLink = String(piLink + F(" TA "));              // Temperature, alarms
      piLink = String(piLink + String(GetIndicator(incSet->isHeatAlarmed(), false, false, true)));
      // CO2 system
      piLink = String(piLink + F(" CM "));              // CO2, mode
      piLink = String(piLink + String(incSet->getCO2Mode(), DEC));
      piLink = String(piLink + F(" CP "));              // CO2, setpoint
      piLink = String(piLink + String(incSet->getCO2SetPoint(), 2));
      piLink = String(piLink + F(" CC "));              // CO2, reading
      piLink = String(piLink + String(incSet->getCO2Level(), 2));
      piLink = String(piLink + F(" CS "));              // CO2, status
      piLink = String(piLink + GetIndicator(incSet->isCO2Open(), incSet->isCO2Stepping(), false, true));
      piLink = String(piLink + F(" CA "));              // CO2, alarms
      piLink = String(piLink + GetIndicator(incSet->isCO2Alarmed(), false, false, true));
      // O2 system
      piLink = String(piLink + F(" OM "));              // O2, mode
      piLink = String(piLink + String(incSet->getO2Mode(), DEC));
      piLink = String(piLink + F(" OP "));              // O2, setpoint
      piLink = String(piLink + String(incSet->getO2SetPoint(), 2));
      piLink = String(piLink + F(" OC "));              // O2, reading
      piLink = String(piLink + String(incSet->getO2Level(), 2));
      piLink = String(piLink + F(" OS "));              // CO2, status
      piLink = String(piLink + GetIndicator(incSet->isO2Open(), incSet->isO2Stepping(), false, true));
      piLink = String(piLink + F(" OA "));              // CO2, alarms
      piLink = String(piLink + GetIndicator(incSet->isO2Alarmed(), false, false, true));
      // Options
      //piLink = String(piLink + F(" LM "));              // Light Mode
      //piLink = String(piLink + String(incSet->getLightMode(), DEC));
      //piLink = String(piLink + F(" LS "));              // Light System
      //piLink = String(piLink + incSet->getLightModule()->GetSerialAPIndicator());
      // Debugging

      #ifdef DEBUG_MEMORY
        piLink = String(piLink + F(" FM "));              // Free memory
        piLink = String(piLink + String(freeMemory(), DEC));
      #endif


      CRC32 crc;
      
      for (int i = 0; i < piLink.length(); i++) {
        crc.update(piLink[i]);
      }
      
      Serial1.print(piLink);
      // CRC to detect bad lines
      Serial1.print(F("||||"));              // Divider
      Serial1.print(crc.finalize(), HEX);
      Serial1.println();
    }
    
  public:
    void SetupPiLink(IncuversSettingsHandler* iSettings) {
      this->incSet = iSettings;
      if (this->incSet->HasPiLink()) {
        Serial1.begin(9600, SERIAL_8E2);
      }
    }

    void DoTick() {
      if (this->incSet->HasPiLink()) {
        CheckForCommands();
        SendStatus();
      }
    }

};

#else
class IncuversPiLink {
  public:
    void SetupPiLink(IncuversSettingsHandler* iSettings) {
    }

    void DoTick() {
    }

};
#endif
