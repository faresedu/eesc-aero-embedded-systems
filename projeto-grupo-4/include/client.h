#ifndef CLIENT_H
#define CLIENT_H

#include <stdlib.h>
#include <iostream>
#include <vector>
#include <cstring>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <unistd.h>
#include "../include/control_msg.h"
#include "../include/label_message.h"
#include <thread>
#include <mutex>

// Define the server IP and port
// 192.168.2.33 
#define SERVER_PORT 5050

// Define size of the buffer in bytes
#define HEADER_SIZE 24
#define STR_MSG_SIZE 20
// Define number of tries to connect to the server
#define MAX_TRIES 50

// This class will be used to receive requests from the server and 
//send the data of the sensors to commander

class Client {
    public:
    // Constructor
        Client();

    // connection to server   
        void connectingToServer();
        void connectingToServer(const char* client_name);
        void connectingToServer(const char* client_name, const char* client_to_connect);

        sockaddr_in CreateSocketAddr(in_addr_t ip, in_port_t port);
    
    // disconnection from wifi and server
        void disconnectFromServer();
    
    // data functions - sending
        void sendingMsg(const std::string& message);

        void sendingMsg(const std::string& command, 
                        const std::string& arg1, 
                        const std::string& arg2);
        
        void sendingMsg(const uint8_t* buffer, 
                        const std::string& type_message, 
                        const int content_size);
        
    // header functions
        std::array<uint8_t, HEADER_SIZE> packHeader(const int msg_size, const std::string& type_message) const;
        std::pair<int, std::string> unpackHeader(const std::array<uint8_t, HEADER_SIZE>& header) const;

    // data functions - receiving
        void receiveLoop();
        void receiveHeader();
        void receivingMsg(const int msg_size, const std::string& type_message);

        bool connected(){return _client.is_alive;}

        char* get_client_id(){return (char*)_client.client_id.c_str();}

        char* get_client_peer(){return (char*)_client.client_peer.c_str();}

        void checkOperation(int result, std::string errorMsg);

        void handleControlMsg(const std::array<uint8_t, CONTROL_MSG_BUFFER>& control_msg);


        ~Client();

    private:
    // WiFi client object        
        int client_socket;
        sockaddr_in server_address;
    
        // Buffer to store the data
        struct Header {
            uint32_t msg_size;
            char type_message[20];
        };

        struct client_pattern{
            std::string client_id;
            std::string client_peer;
            bool is_alive = false;

        };

        client_pattern _client;

        std::mutex _mutex;

        void sendBytes(const uint8_t* buffer, int content_size);

};

#endif // CLIENT_H