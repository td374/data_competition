import xarray as xr
import matplotlib.pyplot as plt
import numpy as np

# 1. 读取 nc 文件
ds = xr.open_dataset("beijing_ndvi_2019.nc")

# 2. 查看数据结构
print("=" * 50)
print("数据集概览：")
print("=" * 50)
print(ds)
print("\n")

# 3. 查看 NDVI 变量的基本信息（变量名是 'var'，不是 'ndvi'）
print("=" * 50)
print("NDVI 信息：")
print("=" * 50)
ndvi = ds['var']  # ⬅️ 关键修改：变量名是 'var'
print(f"形状: {ndvi.shape}")
print(f"最小值: {ndvi.min().values:.4f}")
print(f"最大值: {ndvi.max().values:.4f}")
print(f"平均值: {ndvi.mean().values:.4f}")
print(f"标准差: {ndvi.std().values:.4f}")
print("\n")

# 4. 绘制 NDVI 图（取第一张影像，即第一个时间点）
plt.figure(figsize=(10, 8))
# ndvi 的形状是 (t, y, x)，我们取 t=0 来画第一张图
im = plt.imshow(ndvi[0, :, :].values, cmap='RdYlGn', vmin=-0.1, vmax=0.8)
plt.colorbar(im, label='NDVI')
plt.title('Beijing NDVI - Summer 2019 (First Image)')
plt.xlabel('Pixel X')
plt.ylabel('Pixel Y')

# 保存图片
plt.savefig('beijing_ndvi_2019.png', dpi=150, bbox_inches='tight')
print("✅ NDVI 图已保存为 beijing_ndvi_2019.png")

plt.show()