# Cluster Datasets

This page documents the available spatial cluster geopackages and the corresponding RECOM (Regional Ecological Oceanography Model) marine heatwave datasets for each cluster.

---

## Available Clusters & Geopackages

The following table lists the spatial cluster geopackage datasets used for domain definitions.

| Cluster Name | IS Store Handle ID |
| :--- | :--- |
| `Moore` | [`102.100.100/481718`](https://hdl.handle.net/102.100.100/481718) |
| `Davies` | [`102.100.100/713249`](https://hdl.handle.net/102.100.100/713249)|
| `Lizard` | [`102.100.100/713245`](https://hdl.handle.net/102.100.100/713245) |
| `Heron` | [`102.100.100/713247`](https://hdl.handle.net/102.100.100/713247) |

---

## RECOM Datasets

Each cluster requires corresponding RECOM files containing spatial marine heatwave patterns. Ensure the filenames or patterns match the expected structure:

| Cluster Name | IS Store Handle ID | Expected File Pattern |
| :--- | :--- | :--- |
| `Moore` | [`102.100.100/481718`](https://hdl.handle.net/102.100.100/481718) | `*Moore*_*_dhw*.nc` |
| `Davies` | [`102.100.100/485144`](https://hdl.handle.net/102.100.100/485144) | `*Cairns*_*_dhw*.nc` |
| `Lizard` | [`102.100.100/485092`](https://hdl.handle.net/102.100.100/485092) | `*Lizard*_*_dhw*.nc` |
| `Heron` | [`102.100.100/484974`](https://hdl.handle.net/102.100.100/484974) | `*Heron*_*_dhw*.nc` |

> [!NOTE]
> During DHW generation, the generator automatically globs the RECOM directory using the pattern `*{cluster_name}*_*_dhw*.nc` to find the marine heatwave spatial maps.
