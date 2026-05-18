template <typename T>
struct Box {
  typename T::missing value;
};

int main()
{
  Box<int> box;
  return 0;
}
