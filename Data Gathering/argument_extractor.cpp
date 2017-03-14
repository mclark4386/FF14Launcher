//Program Arguments Extractor
//Copyright Arthur Moore 2016
//BSD 3 Clause License
//Use this to check what the launcher is passing to ffxiv.exe
//This can be compiled online at http://www.onlinecompiler.net/

#include <string>
#include <iostream>
#include <fstream>

int main(int argc, char * argv[])
{
    std::string program_name_and_path = argv[0];
    //Note:  The online compiler has problems with "\\" (The backslash character) so I had to use the ascii code instead
    std::string program_name = program_name_and_path.substr( program_name_and_path.find_last_of( char(0x5c) )+1 );
    std::string out_file_name = program_name +"_arguments.txt";

    std::ofstream out_file(out_file_name.c_str());

    std::cerr << "Outputting all arguments to file:  " << program_name_and_path << std::endl;

    for(int i=0;i<argc;i++)
    {
        std::cout << argv[i] << std::endl;
        out_file << argv[i] << std::endl;
    }


    out_file.close();
    return 0;
}
