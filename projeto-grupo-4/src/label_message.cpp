#include "../include/label_message.h"


LabelMessage::LabelMessage(const std::string& label, const std::string& data)
                                       : label(label), data(data){}


std::array<uint8_t, STRING_BUFFER + LABEL_BUFFER> LabelMessage::pack_msg() const{
    if (label.empty()) {
        throw std::runtime_error("label must be set before serialization");
    }

    if (data.empty()) {
        throw std::runtime_error("Data must be set before serialization");
    }

    std::array<uint8_t, STRING_BUFFER + LABEL_BUFFER> buffer;

    LabelMessagePack msg;
    
    std::strncpy(msg.label_string, formatMessage(label, LABEL_BUFFER).c_str(), LABEL_BUFFER);
    std::strncpy(msg.data_string, formatMessage(data, STRING_BUFFER).c_str(), STRING_BUFFER);

    std::memcpy(buffer.data(), &msg, STRING_BUFFER + LABEL_BUFFER);

    return buffer;
}


LabelMessage LabelMessage::unpack_msg(const std::array<uint8_t, STRING_BUFFER + LABEL_BUFFER>& data) {
    LabelMessagePack msg;
    std::memcpy(&msg, data.data(), STRING_BUFFER + LABEL_BUFFER);

    LabelMessage tempMsg("", "");
    std::strncpy(msg.label_string, tempMsg.removingPadding(msg.label_string).c_str(), LABEL_BUFFER);
    std::strncpy(msg.data_string, tempMsg.removingPadding(msg.data_string).c_str(), STRING_BUFFER);

    return LabelMessage(msg.label_string, msg.data_string);
}

std::string LabelMessage::formatMessage(const std::string& message, int size_msg) const {
    std::string formattedMessage = message;
    if (formattedMessage.length() < size_msg) {
        return formattedMessage + std::string(size_msg - formattedMessage.length(), '\x00');
    } else {
        return formattedMessage.substr(0, size_msg);
    }
}

std::string LabelMessage::removingPadding(const std::string& message) const{
    std::string formattedMessage = message;
    return formattedMessage.substr(0, formattedMessage.find('\x00'));
}

void LabelMessage::display() const {
    std::cout << "[LabelMessage] " << label << ": " << data << std::endl;
}