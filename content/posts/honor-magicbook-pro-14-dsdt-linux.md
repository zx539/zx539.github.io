---
title: "给荣耀 MagicBook Pro 14 2025 国内版修复 DSDT：先测试，再交给 GRUB 持久加载"
date: "2026-11-13T00:00:00+08:00"
draft: false
summary: "记录 Honor MagicBook Pro 14 2025 国内版在 Linux 下替换 DSDT 的过程：如何选对 AML、临时验证补丁，以及为什么持久化要配置 GRUB 而不是 dracut。"
tags: ["Linux", "ACPI", "GRUB", "Fedora", "荣耀笔记本", "故障排查"]
---

在 Honor MagicBook Pro 14 2025 国内版上安装或启动 Linux 时，固件提供的 ACPI DSDT 可能让 USB 控制器和设备无法正常工作。针对这个问题，仓库 [honor-fmb-p-dsdt](https://github.com/denis-bb/honor-fmb-p-dsdt) 提供了修改后的 DSDT 表。

这次修复分成两个阶段：先从 GRUB 临时加载补丁，确认系统和 USB 工作正常；再把加载命令加入启动配置。国内版要使用 `dsdt.chinese.aml`，不能和全球版文件互换。

## 先选对 AML 文件

仓库同时提供中国版和全球版的 AML：

| 机型版本 | 文件 |
| --- | --- |
| 中国版 | `dsdt.chinese.aml` |
| 全球版 | `dsdt.global.aml` |

两份文件不只是名称不同，表中的 OEM revision 和若干 ACPI 内存区域地址也不同。对于国内版机器，应从仓库取得 `dsdt.chinese.aml`。下载后可以用 SHA-256 核对文件：

```bash
sha256sum dsdt.chinese.aml
```

仓库当前中国版文件的摘要是：

```text
937dbce3e6ab47f9f3c2c1818df8c07579771019a9543e8c97dcdb0cfdbdb6a4
```

## 补丁改了什么

主要改动是移除一个声明为 `NTAG0001` 的 NFC 设备节点 `NFC0`。该节点描述了 I²C 地址和 GPIO 中断，但在目标机器上属于不需要的设备记录。

补丁还清理了若干重复或无效的 `External` 声明，以及 XHCI 电源方法的外部调用。中国版和全球版分别保留在仓库中，以匹配各自 BIOS 导出的 DSDT。

## 先通过 GRUB 临时测试

将中国版 AML 放到 `/boot`：

```bash
sudo install -m 0644 dsdt.chinese.aml /boot/dsdt.aml
```

重启进入 GRUB 菜单，选中 Linux 启动项并按 `e` 编辑。在启动项中 `linux` 命令之前插入：

```text
acpi /dsdt.aml
```

按 `Ctrl+X` 或 `F10` 启动。这个修改只作用于本次启动；重启后 GRUB 菜单会恢复原状，适合先验证补丁。

进入系统后检查 USB 设备和控制器是否正常，例如：

```bash
lsusb
dmesg | grep -i -E 'ACPI|DSDT|xhci|usb'
```

也应确认键盘、鼠标、安装介质等实际使用到的设备可用。只有临时加载后运行正常，才继续做持久配置。

## 持久化应改 GRUB

`acpi /dsdt.aml` 是 GRUB 命令。它需要在内核启动前由 GRUB 执行，因此持久化应放进 GRUB 启动项；不需要修改 dracut。dracut 负责生成 initramfs，而这里使用的是 GRUB 从 `/boot` 读取 AML 并替换固件 DSDT 的方式。

具体配置位置取决于发行版和 GRUB 启动模式：

- Debian/Ubuntu 通常由 `/etc/grub.d/40_custom` 生成自定义启动项，之后运行 `sudo update-grub`。
- Fedora 使用 GRUB 2 和 BLS 启动项，配置文件和生成方式与 Debian/Ubuntu 不同。应按当前系统的 GRUB/BLS 配置添加或调整启动项，并用系统提供的命令重新生成配置。

自定义启动项的关键是把 `acpi /dsdt.aml` 放在对应启动项的 `linux` 命令之前。不要把 GRUB 命令直接追加到一个不在 `menuentry` 内的文件末尾，也不要只因能临时启动就假定永久菜单已经包含该命令。配置后先检查生成的 GRUB 配置中启动项顺序和 AML 命令，再重启验证。

保留一个不加载补丁的普通启动项，便于补丁出现问题时回退。升级内核后也要确认自定义启动项仍指向有效的内核和 initramfs。

## 几个实际注意点

- `/boot/dsdt.aml` 必须存在，并且 GRUB 能从其所在分区读取。
- 临时启动时如果提示找不到文件，检查文件路径、GRUB 的根分区和 `/boot` 是否为独立分区。
- 中国版和全球版 AML 不要混用；BIOS 或机型变化时，重新确认补丁适用范围。
- 进入系统后仍应检查 USB、休眠和唤醒等自己依赖的硬件功能。
- 如果需要撤销，先从 GRUB 选择未修改的启动项，再移除加载命令和 `/boot/dsdt.aml`。

这次最重要的经验是把测试和持久化分开：先用一次性 GRUB 编辑验证正确的 DSDT 能解决问题，再根据发行版的启动配置把同一条 ACPI 加载命令写入对应启动项。这样 dracut 无需参与，回退路径也更清楚。
