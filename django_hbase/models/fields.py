class HBaseField:
    field_type = None

    def __init__(self, reverse=False, column_family=None):
        self.reverse = reverse
        # column_family 来表示此field是column field而不是rowkey
        self.column_family = column_family
        #TODO: 增加is_required 属性，默认为true， default属性，默认为None， 并在HBaseModel中做相应处理，抛出相应异常


class IntegerField(HBaseField):
    field_type = 'int'

    def __init__(self, *args, **kwargs):
        super(IntegerField, self).__init__(*args, **kwargs)


class TimestampField(HBaseField):
    field_type = 'timestamp'

    def __init__(self, *args, **kwargs):
        super(TimestampField, self).__init__(*args, **kwargs)
