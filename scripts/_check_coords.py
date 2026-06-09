import pandas as pd, numpy as np
old = pd.read_csv(r"C:\Users\28129\Desktop\共享1-数据收集与核对\scripts\company_coordinates.csv")
new = pd.read_csv(r"C:/Users/28129/xwechat_files/wxid_mo5dfy33ekqs22_b425/temp/RWTemp/2026-06/3b129a93c0a4b421999d60e0190f7001/company_coordinates_70.csv")
m = pd.merge(old, new, left_on="name", right_on="company_name", how="inner")
m["lat_diff"] = abs(m["lat_x"] - m["lat_y"])
m["lon_diff"] = abs(m["lon_x"] - m["lon_y"])
m["dist_km"] = ((m["lat_diff"]*111)**2 + (m["lon_diff"]*111*np.cos(np.radians(m["lat_x"])))**2)**0.5
print("Matched:", len(m))
print("Exact match:", (m["dist_km"] < 0.001).sum())
print("Within 1km:", (m["dist_km"] < 1).sum())
print("Within 10km:", (m["dist_km"] < 10).sum())
big = m[m["dist_km"] > 10]
if len(big):
    print("\nBig diff (>10km):")
    for _, r in big.iterrows():
        print("  {}  old=({},{})  new=({},{})  {:.1f}km".format(
            r["name"][:25], r["lat_x"],r["lon_x"], r["lat_y"],r["lon_y"], r["dist_km"]))