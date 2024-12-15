#include "../include/client.h"
#include <functional>

Client::Client() {
    this->client_socket = socket(AF_INET, SOCK_STREAM, 0);
    checkOperation(this->client_socket, "Socket creation failed");

    this->server_address = CreateSocketAddr(inet_addr("127.0.0.1"), htons(SERVER_PORT)); 

}

sockaddr_in Client::CreateSocketAddr(in_addr_t ip, in_port_t port) {
    sockaddr_in address;
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = ip;
    address.sin_port = port;
    return address;
}

void Client::checkOperation(int result, std::string errorMsg){
    if (result < 0){
        std::cerr << errorMsg << std::endl;
        exit(1);
    }
}

void Client::connectingToServer() {    
    while (this->_client.is_alive == false){
        std::cout << "Trying to connect to server..." << std::endl;
        
        int result = connect(this->client_socket, (struct sockaddr*)&this->server_address, sizeof(this->server_address));
        
        if (result < 0) {
            std::cerr << "Error connecting to server. Retrying in 2 seconds..." << std::endl;
            std::this_thread::sleep_for(std::chrono::seconds(2));
            continue;
        }

        std::this_thread::sleep_for(std::chrono::seconds(2));
        
        if (result == 0) {
            this->_mutex.lock();
            this->_client.is_alive = true;
            this->_mutex.unlock();}
            
        
    }

    std::cout << "Connected to server" << std::endl;
    std::thread receive_thread(std::bind(&Client::receiveLoop, this));
    receive_thread.join();
}

void Client::connectingToServer(const char* client_name) {
    this->_client.client_id = client_name;
    this->connectingToServer();

    // Send a message to the server to register the client
    std::array<uint8_t, CONTROL_MSG_BUFFER> _internal_msg = ControlMsg("change_id", _client.client_id, "").packing();
    sendingMsg(_internal_msg.data(), "ControlMsg", CONTROL_MSG_BUFFER);
}

void Client::connectingToServer(const char* client_name, const char* client_to_connect) {
    this->_client.client_id = client_name;
    this->_client.client_peer = client_to_connect;
    this->connectingToServer();

    // Send a message to the server to register the client
    std::array<uint8_t, CONTROL_MSG_BUFFER> _im_id = ControlMsg("/change_id", _client.client_id, "").packing();
    sendingMsg(_im_id.data(), "ControlMsg", CONTROL_MSG_BUFFER);

    // Send a message to the server to register the client
    std::array<uint8_t, CONTROL_MSG_BUFFER> _im_connect = ControlMsg("/change_peer", _client.client_peer, "").packing();
    sendingMsg(_im_connect.data(), "ControlMsg", CONTROL_MSG_BUFFER);
}

void Client::receiveLoop(){
    while (this->_client.is_alive == true){
        receiveHeader();
    }
}

void Client::receiveHeader(){
    int received = 0;
    ssize_t chunk = 0;
    std::array<uint8_t, HEADER_SIZE> header;
    
       // Loop para receber o cabeçalho em pedaços
    while (received < HEADER_SIZE) {
        chunk = recv(client_socket, header.data() + received, HEADER_SIZE - received, 0);

        if (chunk < 0) {
            std::cerr << "Erro ao receber cabeçalho: A conexão foi redefinida pelo peer." << std::endl;
            disconnectFromServer();
        }

        if (chunk == 0) {
            std::cerr << "Erro ao receber cabeçalho: A conexão foi fechada pelo servidor." << std::endl;
            disconnectFromServer();
        }

        received += chunk;
    }

    std::pair<int, std::string> header_info = unpackHeader(header);

    std::cout << header_info.second.substr(0, 8) << std::endl;
    receivingMsg(header_info.first, header_info.second.substr(0, header_info.second.find('\x00')));
}

void Client::receivingMsg(const int msg_size, const std::string& type_message){
    int bytes_length = msg_size;
    int chunk = 0;
    std::vector<uint8_t> buffer;
    buffer.resize(bytes_length);  // Allocate exact size

    int received = 0;
    while (received < bytes_length) {
        chunk = recv(this->client_socket, buffer.data() + received, bytes_length - received, 0);
        
        if (chunk <= 0) {
            if (chunk == 0) {
                std::cout << "Connection closed by server" << std::endl;
            } else {
                std::cout << "Error receiving data from server: " << strerror(errno) << std::endl;
            }
            disconnectFromServer();
            return;
        }

        received += chunk;
    }

    if (type_message == "ControlMsg"){
        std::array<uint8_t, CONTROL_MSG_BUFFER> buffer_array;
        std::memcpy(buffer_array.data(), buffer.data(), CONTROL_MSG_BUFFER);
        handleControlMsg(buffer_array);
    }
    else if (type_message.substr(0, 8) == "LabelStr"){
        std::array<uint8_t, LABEL_BUFFER + STRING_BUFFER> buffer_array;
        std::memcpy(buffer_array.data(), buffer.data(), STRING_BUFFER + LABEL_BUFFER);
        LabelMessage msg = LabelMessage::unpack_msg(buffer_array);

        msg.display();
    }

    else{
        std::cerr << "Unknown message type" << std::endl;}
}

void Client::handleControlMsg(const std::array<uint8_t, CONTROL_MSG_BUFFER>& control_msg){
    ControlMsg msg = ControlMsg::unpacking(control_msg);
    
    this->_mutex.lock();

    if (msg.getName() == "/change_id"){
        this->_client.client_id = msg.getArg1();
        std::cout << "Client ID changed to " << this->_client.client_id << std::endl;
    }
    else if (msg.getName() == "/change_peer"){
        this->_client.client_peer = msg.getArg1();
        std::cout << "Client peer changed to " << this->_client.client_peer << std::endl;
    }

    else if (msg.getName() == "/end_connection"){
        std::cout << "Disconnecting from server..." << std::endl;
        this->_client.is_alive = false;
        disconnectFromServer();
    }

    else if (msg.getName() == "/peer_lost"){
        std::cout << "Peer lost connection" << std::endl;
        this->_client.client_peer = "broadcast";
    }   

    else{
        std::cerr << "Unknown control message" << std::endl;
    }

    this->_mutex.unlock();

}

void Client::sendingMsg(const uint8_t* buffer, const std::string& type_message, const int content_size){
    std::array<uint8_t, HEADER_SIZE> header = packHeader(content_size, type_message);
    sendBytes(header.data(), HEADER_SIZE);
    sendBytes(buffer, content_size);
}

void Client::sendingMsg(const std::string& message){
    std::array<uint8_t, STRING_BUFFER + LABEL_BUFFER> buffer = LabelMessage(this->_client.client_id, message).pack_msg();
    sendingMsg(buffer.data(), "LabelMsg", STRING_BUFFER + LABEL_BUFFER);
}

void Client::sendingMsg(const std::string& command, const std::string& arg1, const std::string& arg2){
    std::array<uint8_t, CONTROL_MSG_BUFFER> buffer = ControlMsg(command, arg1, arg2).packing();
    sendingMsg(buffer.data(), "ControlMsg", CONTROL_MSG_BUFFER);
}

void Client::sendBytes(const uint8_t* buffer, int content_size){
    // Send a buffer to the server
    int bytes_sent = 0;
    while (bytes_sent < content_size){
        bytes_sent = send(this->client_socket, buffer, content_size, 0);
        if (bytes_sent < 0){
            std::cerr << "Error sending data to server" << std::endl;
            break;
        }
    }
}

std::array<uint8_t, HEADER_SIZE> Client::packHeader(const int msg_size, const std::string& type_message) const {
    // Create a buffer to store the header
    Header header;
    header.msg_size = htonl(msg_size);
    std::memcpy(header.type_message, type_message.c_str(), type_message.size());
    std::memset(header.type_message + type_message.size(), ' ', 20 - type_message.size());

    // Convert Header to std::array<uint8_t, HEADER_SIZE>
    std::array<uint8_t, HEADER_SIZE> header_array;
    std::memcpy(header_array.data(), &header, HEADER_SIZE);
    return header_array;
}  

std::pair<int, std::string> Client::unpackHeader(const std::array<uint8_t, HEADER_SIZE>& header) const {
    // Extract the message size and type from the header
    Header header_struct;
    std::memcpy(&header_struct, header.data(), HEADER_SIZE);

    // Convert message size to host byte order
    int msg_size = ntohl(header_struct.msg_size);

    // Convert type message to string
    std::string type_message(header_struct.type_message, 20);
    
    // remove padding
    type_message.substr(0, type_message.find('\x00'));
    
    return {msg_size, type_message};
}

void Client::disconnectFromServer() {
    close(this->client_socket);
}

Client::~Client() {
    close(this->client_socket);
}