# -*- coding: utf-8 -*-
"""
Master Pipeline Runner
Chains all analysis steps in order. Run after data collection is complete.

Usage:
  python pipeline.py [--skip-financial] [--skip-esg] [--skip-gee]
"""
import os, sys, argparse

ROOT = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(ROOT, "..", "outputs")

def run_step(name, script, condition=True):
    """Run a pipeline step with status reporting."""
    if not condition:
        print(f"  [SKIP] {name}")
        return True
    
    path = os.path.join(SCRIPTS, script)
    if not os.path.exists(path):
        print(f"  [MISS] {name} - script not found: {path}")
        return False
    
    print(f"\n{'='*60}")
    print(f"  STEP: {name}")
    print(f"{'='*60}")
    
    # Run as subprocess to isolate each step
    import subprocess
    result = subprocess.run(
        ["python", path],
        capture_output=False,  # show output in real time
        text=True,
        cwd=SCRIPTS
    )
    
    if result.returncode == 0:
        print(f"  [OK] {name} completed")
        return True
    else:
        print(f"  [FAIL] {name} returned code {result.returncode}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Full analysis pipeline")
    parser.add_argument("--skip-financial", action="store_true", help="Skip financial data collection")
    parser.add_argument("--skip-esg", action="store_true", help="Skip ESG text extraction")
    parser.add_argument("--skip-gee", action="store_true", help="Skip GEE remote sensing")
    parser.add_argument("--skip-green-factory", action="store_true", help="Skip green factory check")
    parser.add_argument("--skip-dashboard", action="store_true", help="Skip dashboard launch")
    args = parser.parse_args()
    
    print("="*60)
    print("  多模态漂绿识别与信贷风险预警 - 分析管道")
    print("="*60)
    
    steps = [
        ("1. 绿色工厂核验",        "check_green_factory.py",        not args.skip_green_factory),
        ("2. ESG文本提取与分析",    "esg_text_analysis.py",         not args.skip_esg),
        ("3. 财务数据采集",         "batch_financials.py",          not args.skip_financial),
        ("4. 财务指标计算",         "calc_financial_indicators.py", True),
        ("5. 遥感数据提取 (GEE)",   "gee_remote_sensing.py",        not args.skip_gee),
        ("6. GWI漂绿指数合成",      "build_gwi.py",                 True),
        ("7. 违约预测模型训练",     "train_models.py",              True),
    ]
    
    for name, script, condition in steps:
        ok = run_step(name, script, condition)
        if not ok and name in ["6. GWI漂绿指数合成", "7. 违约预测模型训练"]:
            print(f"\n  [STOP] Critical step '{name}' failed. Pipeline stopped.")
            break
    
    print(f"\n{'='*60}")
    print("  Pipeline complete!")
    print(f"  输出文件: {SCRIPTS}")
    print(f"{'='*60}")
    
    if not args.skip_dashboard:
        print("\n启动Streamlit沙盘: streamlit run dashboard.py")

if __name__ == "__main__":
    main()
