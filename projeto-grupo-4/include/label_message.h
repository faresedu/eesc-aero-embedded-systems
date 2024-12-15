#ifndef STRING_MSG
#define STRING_MSG

#include <stdlib.h>
#include <iostream>
#include <array>
#include <cstring>
#include <stdexcept>
#include <string>
#include <vector>

#define LABEL_BUFFER 20
#define STRING_BUFFER 80


class LabelMessage{
    public:
        LabelMessage(const std::string& label = NULL, const std::string& data = NULL);

        std::array<uint8_t, STRING_BUFFER + LABEL_BUFFER> pack_msg() const;
        static LabelMessage unpack_msg(const std::array<uint8_t, (STRING_BUFFER + LABEL_BUFFER)>& data);

        std::string removingPadding(const std::string& message) const;
        void display() const;

        std::string formatMessage(const std::string& message, int size_msg) const;

    private:

        std::string label;
        std::string data;

        mutable int data_size = 0;

        struct LabelMessagePack{
            char label_string[LABEL_BUFFER];
            char data_string[STRING_BUFFER];
        };

};

#endif