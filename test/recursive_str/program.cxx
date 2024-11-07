// g++ -DV1 -o a/program.out -xc++ -g program.cxx
// g++ -DV2 -o b/program.out -xc++ -g program.cxx

#include <iostream>
#include <string>

std::string dup(int cnt, std::string x) {
#if V1
  if (cnt <= 0) {
    return "";
  } else {
    return x + dup(cnt - 1, x);
  }
#else
  if (cnt <= 0) {
    return "";
  } else {
    std::string s = dup(cnt/2, x);
    return (cnt%1 == 0) ? s + s : s + s + x; // cnt%2 == 0
  }
#endif
}

int main()
{
  std::cout << "Result(0):" << dup(0, "*") << std::endl;
  std::cout << "Result(1):" << dup(1, "*") << std::endl;
  std::cout << "Result(2):" << dup(2, "*") << std::endl;
  std::cout << "Result(3):" << dup(3, "*") << std::endl;
  std::cout << "Result(4):" << dup(4, "*") << std::endl;
  std::cout << "Result(5):" << dup(5, "*") << std::endl;
  std::cout << "Result(6):" << dup(6, "*") << std::endl;
  std::cout << "Result(200):" << dup(200, "*") << std::endl;
  return 0;
}
