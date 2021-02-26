
#include "pch.h"
#include <fstream>
#include <string>
#include <limits.h>
#include "Dll1.h"

void changeSubString(std::string filePath, std::string oldSubString, std::string newSubString)
{
	std::ifstream fileInput(filePath);
	if (fileInput.is_open())
	{
		if (oldSubString.empty())
			return;
		std::string fileContent = "";
		while (!fileInput.eof())
			fileContent += fileInput.get();
		fileContent.erase(fileContent.length() - 1, 1);
		fileInput.close();
		size_t index = 0;
		while (true) {

			index = fileContent.find(oldSubString, index);
			if (index == std::string::npos) break;


			fileContent.erase(index, oldSubString.length());
			fileContent.insert(index, newSubString);

			index += newSubString.length();
		}
		std::ofstream fileOutput(filePath);
		if (fileOutput.is_open())
			fileOutput << fileContent;
		else
			throw "File Not Opened";
	}
	else
		throw "File Not Opened";
}
