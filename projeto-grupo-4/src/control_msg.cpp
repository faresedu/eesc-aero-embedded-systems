#include "../include/control_msg.h"

// Constructor
ControlMsg::ControlMsg(const std::string& name, 
                       const std::string& arg1, 
                       const std::string& arg2): 
                       name(name), 
                       arg1(arg1), 
                       arg2(arg2){}

// Serialization function
std::array<uint8_t, CONTROL_MSG_BUFFER> ControlMsg::packing() const{
        if (name.empty()) {
            throw std::runtime_error("Name must be set before serialization");
        }

        std::array<uint8_t, CONTROL_MSG_BUFFER> buffer;

        ControlMsgPack msg;
        
        std::strncpy(msg.name, formatMessage(name).c_str(), ARG_SIZE);
        std::strncpy(msg.arg1, formatMessage(arg1).c_str(), ARG_SIZE);
        std::strncpy(msg.arg2, formatMessage(arg2).c_str(), ARG_SIZE);

        std::memcpy(buffer.data(), &msg, CONTROL_MSG_BUFFER);

        return buffer;
        
    }

// Deserialization function
ControlMsg ControlMsg::unpacking(const std::array<uint8_t, CONTROL_MSG_BUFFER>& data) {
        ControlMsgPack msg;
        std::memcpy(&msg, data.data(), CONTROL_MSG_BUFFER);

        ControlMsg tempMsg("", "", "");

        std::string name = tempMsg.removePadding(msg.name).c_str();
        std::string arg1 = tempMsg.removePadding(msg.arg1).c_str();
        std::string arg2 = tempMsg.removePadding(msg.arg2).c_str();

        return ControlMsg(name, arg1, arg2);
       
    }

std::string ControlMsg::formatMessage(const std::string& message) const {
    std::string formattedMessage = message;
    if (formattedMessage.length() < ARG_SIZE) {
        return formattedMessage + std::string(ARG_SIZE - formattedMessage.length(), '\x00');
    } else {
        return formattedMessage.substr(0, ARG_SIZE);
    }
}

std::string ControlMsg::removePadding(const std::string& message) const{
    std::string formattedMessage = message;
    return formattedMessage.substr(0, formattedMessage.find('\x00'));
}

// For displaying the message
void ControlMsg::display() const {
    std::cout << "[ControlMsg] " << name << ": " << arg1 << " " << arg2 << " " << std::endl;
}
