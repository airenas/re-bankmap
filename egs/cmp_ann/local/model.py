import tensorflow as tf


def create_model(inp):
    l_input = tf.keras.layers.Input(shape=inp)
    output = l_input
    output = tf.keras.layers.Dense(100, activation="relu")(output)
    output = tf.keras.layers.Dropout(0.2)(output)
    output = tf.keras.layers.Dense(1, activation="sigmoid")(output)
    model = tf.keras.Model(l_input, output)
    model.summary()
    model.compile(optimizer=tf.keras.optimizers.Adam(), loss=tf.keras.losses.MeanSquaredError())
    return model
