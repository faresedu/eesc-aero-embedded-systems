#ifndef CONTROL_MSG_H
#define CONTROL_MSG_H

#include <stdlib.h>
#include <iostream>
#include <array>
#include <cstring>
#include <stdexcept>
#include <string>

// Define the size of the buffer in bytes
#define CONTROL_MSG_BUFFER 60
#define ARG_SIZE 20

class ControlMsg {
    public:

        ControlMsg(const std::string& name = "", const std::string& arg1 = "", 
                       const std::string& arg2 = "");
        
        std::array<uint8_t, CONTROL_MSG_BUFFER> packing() const;

        static ControlMsg unpacking(const std::array<uint8_t, CONTROL_MSG_BUFFER>& data);
        
        std::string formatMessage(const std::string& message) const;

        std::string removePadding(const std::string& message) const;

        void display() const;

        std::string getName() const { return name; }
        std::string getArg1() const { return arg1; }
        std::string getArg2() const { return arg2; }

    private:
        std::string name;
        std::string arg1;
        std::string arg2;
        
        struct ControlMsgPack {
            char name[20];
            char arg1[20];
            char arg2[20];
        };
};


#endif // MACRO
