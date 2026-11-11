# ffmpeg-a32：歧义 DA 降序证据入口

每组明细按 group 字段连接同目录 S-instances、candidates、candidate-copies 与 commands CSV。
S 实例含 CU、声明、区间、内联/抽象源；候选含完整 PGO 名、C 定义位置、TU 与实际命令日志行。
此表只陈述事实，不作新身份裁决。

| group | 文件 / 名字 | 类别 | S 实例数 | 参考行数 | 并集 DA | 未通过检查 |
|---|---|---|---:|---:|---:|---|
| 1347 | /home/abuild/rpmbuild/BUILD/ffmpeg-8.0.1/libavcodec/rectangle.h / _ZL14fill_rectanglePviiiji | a_different_TU | 121 | 59 | 891793012 | ["empty_leaf_line_set"] |
| 171 | /home/abuild/rpmbuild/BUILD/ffmpeg-8.0.1/libavcodec/cabac_functions.h / _ZL9get_cabacP12CABACContextPh | a_different_TU | 103 | 3 | 647083311 | ["empty_leaf_line_set"] |
| 186 | /home/abuild/rpmbuild/BUILD/ffmpeg-8.0.1/libavcodec/h264_cabac.c / _ZL27decode_cabac_residual_nondcPK11H264ContextP16H264SliceContextPsiiPKhPKji | d_other | 13 | 11 | 87062068 | ["empty_leaf_line_set"] |
| 183 | /home/abuild/rpmbuild/BUILD/ffmpeg-8.0.1/libavcodec/get_bits.h / _ZL8get_bitsP13GetBitContexti | a_different_TU | 2138 | 11 | 182017 | ["empty_leaf_line_set"] |
| 178 | /home/abuild/rpmbuild/BUILD/ffmpeg-8.0.1/libavcodec/get_bits.h / _ZL13get_bits_longP13GetBitContexti | a_different_TU | 221 | 14 | 59133 | ["empty_leaf_line_set"] |
| 181 | /home/abuild/rpmbuild/BUILD/ffmpeg-8.0.1/libavcodec/get_bits.h / _ZL14show_bits_longP13GetBitContexti | a_different_TU | 90 | 8 | 21777 | ["empty_leaf_line_set"] |
| 185 | /home/abuild/rpmbuild/BUILD/ffmpeg-8.0.1/libavcodec/golomb.h / _ZL18get_ue_golomb_longP13GetBitContext | a_different_TU | 81 | 7 | 21777 | ["empty_leaf_line_set"] |
| 182 | /home/abuild/rpmbuild/BUILD/ffmpeg-8.0.1/libavcodec/get_bits.h / _ZL14skip_bits_longP13GetBitContexti | a_different_TU | 122 | 3 | 9333 | ["empty_leaf_line_set"] |
| 184 | /home/abuild/rpmbuild/BUILD/ffmpeg-8.0.1/libavcodec/get_bits.h / _ZL9skip_bitsP13GetBitContexti | a_different_TU | 282 | 5 | 6755 | ["empty_leaf_line_set"] |
| 176 | /home/abuild/rpmbuild/BUILD/ffmpeg-8.0.1/libavcodec/get_bits.h / _ZL10skip_bits1P13GetBitContext | a_different_TU | 67 | 3 | 48 | ["empty_leaf_line_set"] |
| 165 | /home/abuild/rpmbuild/BUILD/ffmpeg-8.0.1/libavcodec/bytestream.h / _ZL22bytestream2_peek_be16uPK14GetByteContext | a_different_TU | 1 | 4 | 24 | ["leaf_line_outside_range"] |
| 166 | /home/abuild/rpmbuild/BUILD/ffmpeg-8.0.1/libavcodec/bytestream.h / _ZL22bytestream2_peek_be24uPK14GetByteContext | a_different_TU | 1 | 4 | 24 | ["leaf_line_outside_range"] |
| 167 | /home/abuild/rpmbuild/BUILD/ffmpeg-8.0.1/libavcodec/bytestream.h / _ZL22bytestream2_peek_be32uPK14GetByteContext | a_different_TU | 1 | 4 | 24 | ["leaf_line_outside_range"] |
| 168 | /home/abuild/rpmbuild/BUILD/ffmpeg-8.0.1/libavcodec/bytestream.h / _ZL22bytestream2_peek_byteuPK14GetByteContext | a_different_TU | 2 | 4 | 24 | ["leaf_line_outside_range"] |
| 169 | /home/abuild/rpmbuild/BUILD/ffmpeg-8.0.1/libavcodec/bytestream.h / _ZL22bytestream2_peek_le16uPK14GetByteContext | a_different_TU | 1 | 4 | 24 | ["leaf_line_outside_range"] |
| 128 | /home/abuild/rpmbuild/BUILD/ffmpeg-8.0.1/libavcodec/bytestream.h / _ZL19bytestream_get_be16PPKh | a_different_TU | 28 | 5 | 20 | ["leaf_line_outside_range"] |
| 129 | /home/abuild/rpmbuild/BUILD/ffmpeg-8.0.1/libavcodec/bytestream.h / _ZL19bytestream_get_be24PPKh | a_different_TU | 4 | 5 | 20 | ["leaf_line_outside_range"] |
| 130 | /home/abuild/rpmbuild/BUILD/ffmpeg-8.0.1/libavcodec/bytestream.h / _ZL19bytestream_get_be32PPKh | a_different_TU | 20 | 5 | 20 | ["leaf_line_outside_range"] |
| 131 | /home/abuild/rpmbuild/BUILD/ffmpeg-8.0.1/libavcodec/bytestream.h / _ZL19bytestream_get_be64PPKh | a_different_TU | 3 | 5 | 20 | ["leaf_line_outside_range"] |
| 132 | /home/abuild/rpmbuild/BUILD/ffmpeg-8.0.1/libavcodec/bytestream.h / _ZL19bytestream_get_bytePPKh | a_different_TU | 55 | 5 | 20 | ["leaf_line_outside_range"] |

累计唯一 DA：1626239275 / 1626239322；比例 0.9999999710989648。至少20组或列出全部。
