import tensorflow as tf
reader = tf.TFRecordReader()
# filenames = glob.glob('*.tfrecords')
filenames = ['~/cant-grader/Training_Job/data/train2.record']
output_dir = '~/cant-grader/record_dump'

filename_queue = tf.train.string_input_producer(
   filenames)
_, serialized_example = reader.read(filename_queue)
feature_set = {
    'image/height': tf.FixedLenFeature([], tf.int64),
    'image/width': tf.FixedLenFeature([], tf.int64),
    'image/filename': tf.VarLenFeature(tf.string),
    'image/source_id': tf.VarLenFeature(tf.string),
    'image/encoded': tf.VarLenFeature(tf.string),
    'image/format': tf.VarLenFeature(tf.string),
    'image/object/bbox/xmin': tf.FixedLenSequenceFeature([1], tf.float32, allow_missing=True),
    'image/object/bbox/xmax': tf.FixedLenSequenceFeature([1], tf.float32, allow_missing=True),
    'image/object/bbox/ymin': tf.FixedLenSequenceFeature([1], tf.float32, allow_missing=True),
    'image/object/bbox/ymax': tf.FixedLenSequenceFeature([1], tf.float32, allow_missing=True),
    'image/object/class/text': tf.VarLenFeature(tf.string),
    'image/object/class/label': tf.FixedLenFeature([], tf.int64)
              }
#    'image/filename': tf.VarLenFeature([], tf.string),

features = tf.parse_single_example(serialized_example,
                                   features=feature_set)
image = features['image/encoded']

with tf.Session() as sess:
    print(sess.run(image))
