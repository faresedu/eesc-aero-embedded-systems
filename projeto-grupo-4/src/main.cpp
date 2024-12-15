#include "../include/client.h"
#include <iostream>
#include <chrono>
#include <thread>
#include "../include/label_message.h"


int main() {
    Client client;

    client.connectingToServer();

    while(true){
        std::array<uint8_t, STRING_BUFFER + LABEL_BUFFER> buffer = LabelMessage(client.get_client_id(), "Hello World").pack_msg();
        client.sendingMsg(buffer.data(), "LabelMsg", STRING_MSG + LABEL_BUFFER);

        std::this_thread::sleep_for(std::chrono::seconds(4));
    }

    
    
}