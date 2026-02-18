#include <iostream>
#include <iomanip>
#include <fstream>
#include <string>
#include <vector>
#include <cmath>

//class hierarchy?
//make sure colmap's image.txt is in the same dir as this script.
//you can get img.txt by running colmap model_converter with output_type as TXT, set input path as folder with images.bin

/*
The reconstructed pose of an image is specified as the projection from world to the camera coordinate system of an image
using a quaternion (QW, QX, QY, QZ) and a translation vector (TX, TY, TZ). 
The quaternion is defined using the Hamilton convention...
https://colmap.github.io/format.html
*/
//https://www.andre-gaschler.com/rotationconverter/ for reference

struct Quaternion{
    std::string imageName = "";
    double qw = 0;
    double qx = 0;
    double qy = 0;
    double qz = 0;
    Quaternion(std::string imageName, double qw, double qx, double qy, double qz){
        this->imageName = imageName;
        this->qw = qw;
        this->qx = qx;
        this->qy = qy;
        this->qz = qz;
    }
    void printQuaternion(){
        std::cout << "Image Name: " << imageName << std::endl; 
        std::cout << std::setprecision(16);
        std::cout << "qw: " << (qw) << std::endl; 
        std::cout << "qx: " << (qx) << std::endl; 
        std::cout << "qy: " << (qy) << std::endl; 
        std::cout << "qz: " << (qw) << std::endl; 
        std::cout << "------------" << std::endl;
    }
};

struct RotationMatrix{
    std::string imageName = "";
    std::vector<std::vector<double>> rotationMatrix{std::vector<std::vector<double>>(3,std::vector<double>(3,0))};
    //formula from https://en.wikipedia.org/wiki/Conversion_between_quaternions_and_Euler_angles
    RotationMatrix(Quaternion& q){
        this->imageName = q.imageName;
        rotationMatrix[0][0] = 1 - 2 * (pow(q.qy,2) + pow(q.qz,2));
        rotationMatrix[0][1] = 2 * (q.qx*q.qy - q.qw*q.qz);
        rotationMatrix[0][2] = 2 * (q.qw*q.qy + q.qx*q.qz);
        rotationMatrix[1][0] = 2 * (q.qx*q.qy + q.qw*q.qz);
        rotationMatrix[1][1] = 1 - 2 * (pow(q.qx,2) + pow(q.qz,2));
        rotationMatrix[1][2] = 2 * (q.qy*q.qz + q.qw*q.qx);
        rotationMatrix[2][0] = 2 * (q.qx*q.qz + q.qw*q.qy);
        rotationMatrix[2][1] = 2 * (q.qw*q.qx + q.qy*q.qz);
        rotationMatrix[2][2] = 1 - 2 * (pow(q.qx,2) + pow(q.qy,2));
    }
    void printRotationMatrix(){
        std::cout << "Image Name: " << imageName << std::endl;
        for(int i = 0; i < 3; i++){
            for(const auto& j : rotationMatrix[i]){
                std::cout << j << " ";
            }
            std::cout << std::endl;
        }
        std::cout << "------------" << std::endl;
    }
};

struct TaitBryan{
    std::string imageName = "";
    double heading = 0; //z axis, points downward
    double pitch = 0; //y axis, points rightward
    double bank = 0; //x axis, points forward
    //formula from https://www.sedris.org/wg8home/Documents/WG80485.pdf#page=43.5
    TaitBryan(Quaternion& q){
        this->imageName  = q.imageName;
        bank = atan2((q.qy*q.qz + q.qw*q.qx), 0.5 - (pow(q.qx,2) + pow(q.qy,2)));
        pitch = asin(-2*(q.qx*q.qz - q.qw*q.qy));
        heading = atan2((q.qx*q.qy + q.qw*q.qz), 0.5 - (pow(q.qy,2) + pow(q.qz,2)));
    }
    void printTaitBryan(){
        std::cout << "Image Name: " << imageName << std::endl; 
        std::cout << std::setprecision(16);
        std::cout << "Heading (Z-Axis: Downward): " << (heading) << std::endl; 
        std::cout << "Pitch (Y-Axis: Rightward): " << (pitch) << std::endl; 
        std::cout << "Bank (X-Axis: Forward): " << (bank) << std::endl; 
        std::cout << "------------" << std::endl;
    }
};


int main(int argc, char** argv){
    std::ifstream infile("images.txt");
    std::vector<std::string> firstLines;
    bool flag = true;
    for(std::string line; getline(infile, line);){
        if(flag){
            firstLines.push_back(line);
        }
        flag = !flag;
    }
    std::vector<Quaternion> quats;
    std::cout << "Quaternions: " << std::endl;
    for(const auto& s : firstLines){
        size_t firstSpace = s.find(' ');
        size_t secondSpace = s.find(' ', firstSpace + 1);
        size_t thirdSpace = s.find(' ', secondSpace + 1);
        size_t fourthSpace = s.find(' ', thirdSpace + 1);
        size_t fifthSpace = s.find(' ', fourthSpace + 1);
        size_t lastSpace = s.rfind(' ');
        try{
            quats.emplace_back(
                s.substr(lastSpace, s.size()-lastSpace),
                std::stod(s.substr(firstSpace, secondSpace-firstSpace-1)),
                std::stod(s.substr(secondSpace, thirdSpace-secondSpace-1)),
                std::stod(s.substr(thirdSpace, fourthSpace-thirdSpace-1)),
                std::stod(s.substr(fourthSpace, fifthSpace-fourthSpace-1))
            );
            quats[quats.size()-1].printQuaternion();
        } catch (...) {}
    }
    std::cout << "\nRotation Matrices: " << std::endl;
    std::vector<RotationMatrix> rotMats;
    for(int i = 0; i < quats.size(); i++){
        rotMats.emplace_back(quats[i]);
        rotMats[i].printRotationMatrix();
    }
    std::cout << "\nTait-Bryan Angles (Euler angle Z-Y-X rotation convention): " << std::endl;
    std::vector<TaitBryan> tbs;
    for(int i = 0; i < quats.size(); i++){
        tbs.emplace_back(quats[i]);
        tbs[i].printTaitBryan();
    }

    return 0;
}