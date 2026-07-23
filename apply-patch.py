#!/usr/bin/env python3
import os
import subprocess
import sys
from xml.etree import ElementTree
shared_patches: dict = {
    "android-12.0.0_r32": ["android-12.0.0_r34"],
    "android-13.0.0_r82": ["android-13.0.0_r83"],
    "android-14.0.0_r2": ["android-14.0.0_r11", "android-14.0.0_r15", "android-14.0.0_r21"]
}
def main(src: str, special_path : str | None):
    failed_patches = []
    tag = None
    if not tag:
        print("\033[33mDetect AOSP tag from manifest\033[0m")
        if tag is None:
            manifest_path = f"{src}/.repo/manifests/default.xml"
            if not os.path.exists(manifest_path):
                print("\033[31mManifest file not found, aborting\033[0m")
                exit(1)
            xml_root = ElementTree.parse(manifest_path).getroot()
            tag_raw = None
            for e in xml_root.findall("default"):
                tag_raw = e.get("revision")
            if tag_raw is None:
                print("\033[33mNo tag detected.\033[0m")
                exit(1)
            tag = os.path.basename(tag_raw)
    #Check if in shared patches
    for k, v in shared_patches.items():
        if tag in v:
            print(f"\033[33m[Notice] {tag} shared {k} patches.\033[0m")
            tag = k
            break

    print(f"\033[34m===== AOSP SRC: {src}\033[0m")
    print(f"\033[34m===== AOSP TAG: {tag}\033[0m")
    patch_dir = f"{os.path.dirname(os.path.realpath(sys.argv[0]))}/{tag}"
    if not os.path.exists(patch_dir):
        print(f"\033[33mpatches({patch_dir}) for {tag} not exist\033[0m")
        exit(1)
    for root, dirs, _ in os.walk(str(os.path.join(patch_dir, special_path)) if special_path else patch_dir):
        for dir_ in dirs:
            p = os.path.join(root.replace(patch_dir, "")[1:], dir_)
            if not (patches := [i for i in os.listdir(os.path.join(root, dir_)) if i.endswith(".patch")]):
                continue
            print(f"\033[32mPatching: {p}\033[0m")
            ret = subprocess.run(
                ["git", "-C", f"{src}/{p}", "am", "--reject", *[f"{patch_dir}/{p}/{i}" for i in patches]], stdout=subprocess.PIPE)
            if ret.returncode != 0:
                print(f"\033[31m[ERROR] Patch Failed: {p}\033[0m")
                failed_patches.append(p)
                print(f"\033[33m[Reset] Reset: {p}\033[0m")
                for sp in [
                subprocess.run(
                    ["git", "-C", f"{src}/{p}", "am", "--abort"],
                    stdout=subprocess.PIPE)
                , subprocess.run(
                    ["git", "-C", f"{src}/{p}", "reset", "--hard", "HEAD"],
                    stdout=subprocess.PIPE)
                , subprocess.run(
                    ["git", "-C", f"{src}/{p}", "clean", "-fd",],
                    stdout=subprocess.PIPE)]:
                    if sp.returncode != 0:
                        print(f"\033[31m[ERROR] Reset Failed: {p}, try 'repo sync -f' to sync the official code.\033[0m")
                        break
    if failed_patches:
        print(f"\033[31m[Error Conclusion]Failed to Patch: {failed_patches}\033[0m")
    else:
        print("\033[32mAll patch applied.\033[0m")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"{sys.argv[0]} AOSP-SRC [PATH]")
        exit(1)
    main(sys.argv[1], None if len(sys.argv) < 3 else sys.argv[2])
