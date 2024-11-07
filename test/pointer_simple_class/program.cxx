// g++ -DV1 -o a/program.out -xc++ -g program.cxx
// g++ -DV2 -o b/program.out -xc++ -g program.cxx

#include <iostream>

class Task {
    public:
        int id;
        Task *next;
        Task(int i, Task *n):
            id(i),
            next(n)
        {}
    };

int a3(int i = 3) {
  int * j = new int(2);
  int * k = new int(7);
  std::cout <<  "Ptr:" << j << std::endl;

  return 0;
}


int main()
{
  Task *task_head = new Task(-1, NULL);
  Task *task1 = new Task(1, NULL);
  //Task *task2 = new Task(2, NULL);
  //Task *task3 = new Task(3, NULL);
  //Task *task4 = new Task(4, NULL);
  //Task *task5 = new Task(5, NULL);

  task_head->next = task1;
  //task1->next = task2;
  //task2->next = task3;
  //task3->next = task4;
  //task4->next = task5;

  return 0;
}
