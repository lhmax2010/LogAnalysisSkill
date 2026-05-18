struct demo {
  int present;
};

int read_demo(struct demo *value)
{
  return value->missing;
}
