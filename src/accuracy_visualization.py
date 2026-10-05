import matplotlib.pyplot as plt

accuracy = 98.99

plt.figure(figsize=(6,5))

plt.bar(["Face Recognition Model"], [accuracy])

plt.ylim(0,100)

plt.ylabel("Accuracy (%)")

plt.title("Student Recognition Model Accuracy")

plt.text(
    0,
    accuracy + 1,
    f"{accuracy:.2f}%"
)


plt.show()